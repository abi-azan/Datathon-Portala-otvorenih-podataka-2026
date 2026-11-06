"""docs/DOKUMENTACIJA.md -> docs/DOKUMENTACIJA.html, the document sent to the jury.

    .venv/Scripts/python -m pipeline.dokumentacija

The HTML is laid out for A4 and gets an appendix the Markdown does not carry: every dataset used,
with its publisher, access and links, read from the published api/v1/skupovi.json (so the appendix
can never differ from the list in the product). Print the HTML to PDF from a browser (A4, the
page's own margins); the PDF is committed as docs/DOKUMENTACIJA.pdf, the HTML is not.
"""
import html
import json
import sys
from urllib.parse import urlparse

from . import config

DOCS = config.ROOT / "docs"
DATASETS = config.ROOT / "web" / "public" / "api" / "v1" / "skupovi.json"
FONTS = "../web/node_modules/@fontsource-variable"

CSS = """
@font-face { font-family: 'Public Sans'; font-weight: 100 900; src: url('%(fonts)s/public-sans/files/public-sans-latin-ext-wght-normal.woff2') format('woff2'); unicode-range: U+0100-02BA, U+1E00-1E9F, U+20A0-20C0; }
@font-face { font-family: 'Public Sans'; font-weight: 100 900; src: url('%(fonts)s/public-sans/files/public-sans-latin-wght-normal.woff2') format('woff2'); }
@font-face { font-family: 'Source Serif 4'; font-weight: 200 900; src: url('%(fonts)s/source-serif-4/files/source-serif-4-latin-ext-wght-normal.woff2') format('woff2'); unicode-range: U+0100-02BA, U+1E00-1E9F, U+20A0-20C0; }
@font-face { font-family: 'Source Serif 4'; font-weight: 200 900; src: url('%(fonts)s/source-serif-4/files/source-serif-4-latin-wght-normal.woff2') format('woff2'); }
@page { size: A4; margin: 15mm 15mm 16mm; }
* { box-sizing: border-box; }
body { font: 10.2pt/1.45 'Public Sans', 'Segoe UI', Arial, sans-serif; color: #1a1a18; margin: 0; }
h1, h2 { font-family: 'Source Serif 4', Georgia, serif; color: #0b0b0b; }
h1 { font-size: 23pt; line-height: 1.15; margin: 0 0 4pt; }
h2 { font-size: 14.5pt; margin: 16pt 0 5pt; padding-top: 7pt; border-top: 1pt solid #dedcd5; break-after: avoid; }
p { margin: 0 0 6pt; }
ul, ol { margin: 0 0 6pt; padding-left: 15pt; }
li { margin-bottom: 2.5pt; }
a { color: #0b5d50; text-decoration: none; }
code { font: 8.8pt 'Cascadia Mono', Consolas, monospace; background: #f1efe9; padding: 0 2pt; border-radius: 2pt; }
table { border-collapse: collapse; width: 100%%; margin: 4pt 0 8pt; font-size: 8.8pt; line-height: 1.35; }
th, td { text-align: left; vertical-align: top; padding: 3.5pt 6pt 3.5pt 0; border-bottom: 0.6pt solid #dedcd5; }
th { font-weight: 600; color: #55544f; border-bottom: 1pt solid #b9b7af; }
thead tr:has(th:empty) { display: none; }
tr { break-inside: avoid; }
img { display: block; width: 100%%; margin: 6pt 0 9pt; border: 0.6pt solid #dedcd5; border-radius: 5pt; break-inside: avoid; }
p:has(> img) { break-inside: avoid; }
.prilog { break-before: page; }
.prilog table { font-size: 7.6pt; }
.prilog td:first-child { width: 43%%; }
.domena { color: #6b6a66; }
"""


def appendix(datasets):
    """The table of every dataset used: name, publisher, access, links."""
    rows = []
    for d in datasets:
        if not d.get("koristi_se"):
            continue
        direct = ("poziv API-ja" if d["pristup"].startswith("API") else "datoteka" if d["pristup"].startswith("datoteka")
                  else "model" if d["pristup"] == "model" else "izvor")
        links = [f'<a href="{html.escape(d["portal_url"])}">stranica skupa</a>'] if d.get("portal_url") else []
        if d.get("url"):
            links.append(f'<a href="{html.escape(d["url"])}">{direct}</a>')
        host = urlparse(d.get("portal_url") or d.get("url") or "").netloc.removeprefix("www.")
        rows.append(f"<tr><td>{html.escape(d['naziv'])}</td><td>{html.escape(d['izdavatelj'])}</td>"
                    f"<td>{html.escape(d['pristup'])}</td><td>{' · '.join(links)}<br><span class=\"domena\">{host}</span></td></tr>")
    return ('<section class="prilog"><h2>Prilog: svi korišteni skupovi podataka</h2>'
            f"<p>{len(rows)} skupova, s izdavateljem, načinom pristupa i poveznicama na izvor. Licenca svakog skupa i datum "
            "zadnje izmjene navedeni su u <code>docs/skupovi-podataka.md</code> i u <code>api/v1/skupovi.json</code>.</p>"
            "<table><thead><tr><th>Skup podataka</th><th>Izdavatelj</th><th>Pristup</th><th>Poveznice</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></section>")


def build():
    from markdown_it import MarkdownIt
    if not DATASETS.exists():
        raise SystemExit(f"nema {DATASETS}: prvo pokreni python -m pipeline.publish")
    body = MarkdownIt("commonmark").enable("table").render((DOCS / "DOKUMENTACIJA.md").read_text(encoding="utf-8"))
    datasets = json.loads(DATASETS.read_text(encoding="utf-8"))
    page = ('<!doctype html>\n<html lang="hr"><head><meta charset="utf-8">'
            "<title>Fiskalna karta: tehnička i projektna dokumentacija</title>"
            f"<style>{CSS % {'fonts': FONTS}}</style></head><body>\n{body}\n{appendix(datasets)}\n</body></html>\n")
    dest = DOCS / "DOKUMENTACIJA.html"
    dest.write_text(page, encoding="utf-8")
    print(f"{dest} ({len(page) // 1024} KB, {sum(bool(d.get('koristi_se')) for d in datasets)} skupova u prilogu)")
    return dest


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    build()
