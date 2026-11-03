"""The unit register (šifrarnik): OIB ↔ RKP ↔ official code ↔ name ↔ county for all 576 units.

PR-RAS sheets carry only names. Bilanca carries OIB and RKP. The reference table
data/reference/jls_master.csv carries the 5-digit DGU/DZS code (also used by the
Sudski registar) and structural attributes for the 556 towns and municipalities.
Names are matched within the county, first exactly and then with match_key.
"""
import re
import unicodedata

import pandas as pd

from . import config


def norm_name(s):
    s = str(s).upper().strip()
    s = re.sub(r"\s*-\s*", "-", s)
    return re.sub(r"\s+", " ", s)


def bare_name(full):
    full = norm_name(full)
    for p in ("GRAD ", "OPĆINA "):
        if full.startswith(p):
            return full[len(p):]
    return full


def match_key(name):
    """Loose key for names that differ between sources: bilingual Istrian names,
    en dashes, "SV." abbreviations and county suffixes."""
    s = bare_name(name).replace("–", "-")
    s = re.sub(r"^SV\. ?", "SVETI ", s)
    s = re.sub(r" ZADARSKI$| OPĆINA$", "", s)
    return re.split(r"\s*-\s*", s)[0].strip()


def slugify(s):
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _vrsta_from_name(name):
    n = norm_name(name)
    if n.endswith("ŽUPANIJA"):
        return "zupanija"
    if n.startswith("GRAD "):
        return "grad"
    return "opcina"


def build_units(sheets, bilanca, master):
    """sheets: DataFrame zup_id, sheet, vrsta (one row per PR-RAS sheet).
    bilanca: parsed Bilanca (any year has all 576 rows).
    master: data/reference/jls_master.csv."""
    bil = (bilanca.sort_values("year").groupby("oib").last().reset_index()
           [["oib", "rkp", "zup_id", "naziv_bilanca"]])
    bil["vrsta"] = bil["naziv_bilanca"].map(_vrsta_from_name)
    bil["k_exact"] = bil["naziv_bilanca"].map(bare_name)
    bil["k_loose"] = bil["naziv_bilanca"].map(match_key)

    rows, problems = [], []
    for s in sheets.itertuples():
        cand = bil[(bil.zup_id == s.zup_id) & (bil.vrsta == s.vrsta)]
        hit = cand[cand.k_exact == bare_name(s.sheet)]
        if len(hit) != 1:
            hit = cand[cand.k_loose == match_key(s.sheet)]
        if len(hit) != 1:
            problems.append((s.zup_id, s.sheet, len(hit)))
            continue
        b = hit.iloc[0]
        rows.append({"oib": b.oib, "rkp": b.rkp, "zup_id": s.zup_id, "vrsta": s.vrsta, "naziv_mf": s.sheet})
    if problems:
        raise ValueError(f"PR-RAS sheets without a unique Bilanca match: {problems}")
    u = pd.DataFrame(rows)

    m = master.copy()
    m["oib"] = m["oib"].astype(str).str.zfill(11)
    m["sifra"] = m["jls_code"].astype(str).str.zfill(5)
    u = u.merge(m.drop(columns=["zup_id", "tip", "rkp", "mf_naziv"], errors="ignore"), on="oib", how="left")

    zup_names = (m.assign(zup_id=master["zup_id"].astype(int))
                 .groupby("zup_id")["zupanija"].first().to_dict())
    u["zupanija"] = u["zup_id"].map(zup_names)

    jls = u.vrsta != "zupanija"
    missing = u[jls & u.sifra.isna()]
    if len(missing):
        raise ValueError(f"units without a DGU code: {missing.naziv_mf.tolist()}")
    u.loc[~jls, "sifra"] = u.loc[~jls, "zup_id"].map(lambda z: f"Z{int(z):02d}")
    u["zagreb"] = u["sifra"] == "01333"
    prefix = {"opcina": "Općina ", "grad": "Grad ", "zupanija": ""}
    u["naziv"] = [
        zup_names.get(z, nm.title()) if v == "zupanija"
        else n if n.startswith(prefix[v])            # the master already says "Grad Zagreb"
        else prefix[v] + n
        for v, n, z, nm in zip(u.vrsta, u.naziv, u.zup_id, u.naziv_mf)
    ]
    u["slug"] = u["naziv"].map(slugify)
    if u.slug.duplicated().any():
        dup = u[u.slug.duplicated(keep=False)]
        u.loc[dup.index, "slug"] = dup.slug + "-" + dup.sifra
    cols = ["oib", "rkp", "sifra", "slug", "naziv", "naziv_mf", "vrsta", "zagreb", "zup_id", "zupanija"]
    rest = [c for c in u.columns if c not in cols and c not in ("jls_code", "lau_id")]
    return u[cols + rest].sort_values(["zup_id", "vrsta", "naziv"]).reset_index(drop=True)
