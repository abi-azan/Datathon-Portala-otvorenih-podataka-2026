"""PR-RAS ZIP member names: CP852 without the UTF-8 flag, read by zipfile as CP437."""
import zipfile

import pytest

from pipeline import config, mf

REAL_ZIP = config.RAW / "mf" / "prras.zip"


def test_cp852_name_read_as_cp437_is_fixed():
    assert mf.zip_member_name("01 Zagrebaƒka.xlsx") == "01 Zagrebačka.xlsx"
    assert mf.zip_member_name("20 Me╨imurska.xlsx") == "20 Međimurska.xlsx"


def test_ascii_name_unchanged():
    assert mf.zip_member_name("21 Grad_Zagreb.xlsx") == "21 Grad_Zagreb.xlsx"


def test_utf8_flagged_name_unchanged(tmp_path):
    # "à" exists in CP437 and would turn into "ů" if re-decoded as CP852
    path = tmp_path / "utf8.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("01 voilà.xlsx", b"")
        z.writestr("01 Zagrebačka.xlsx", b"")
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
    assert all(i.flag_bits & 0x800 for i in infos)
    assert [mf.zip_member_name(i.filename, i.flag_bits) for i in infos] == ["01 voilà.xlsx", "01 Zagrebačka.xlsx"]


def test_extract_prras_returns_readable_names(tmp_path):
    # zipfile writes non-ASCII names as UTF-8, so write ASCII placeholders and patch in CP852 bytes
    path = tmp_path / "prras.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("01 Zagreba#ka.xlsx", b"zg")
        z.writestr("14 Osje#ko_baranjska.xlsx", b"old")
        z.writestr("14 Osje#ko_baranjska ispravak.xlsx", b"new")
    raw = path.read_bytes()
    for stem in (b"Zagreba#ka", b"Osje#ko"):
        raw = raw.replace(stem, stem.replace(b"#", "č".encode("cp852")))
    path.write_bytes(raw)
    with zipfile.ZipFile(path) as z:
        assert "01 Zagrebaƒka.xlsx" in z.namelist()  # the mis-decoded form the MF ZIP produces

    files, names = mf.extract_prras(path, tmp_path / "out")
    assert names == {"01": "01 Zagrebačka.xlsx", "14": "14 Osječko_baranjska ispravak.xlsx"}
    assert files["01"].name == "01.xlsx"
    assert files["14"].read_bytes() == b"new"


@pytest.mark.skipif(not REAL_ZIP.exists(), reason="data/raw/mf/prras.zip not downloaded")
def test_real_mf_zip_names():
    with zipfile.ZipFile(REAL_ZIP) as z:
        names = [mf.zip_member_name(i.filename, i.flag_bits) for i in z.infolist()]
    assert any("Zagrebačka" in n for n in names)
    assert any("Osječko" in n for n in names)
