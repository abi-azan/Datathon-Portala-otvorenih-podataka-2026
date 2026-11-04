"""MCP server definition (MCP Python SDK 2.x, MCPServer, formerly FastMCP).

Tool names and descriptions are in Croatian, because the users ask in Croatian. Every tool is
read-only and returns JSON; an error is a {"greska": ...} object, never an exception.
"""

from __future__ import annotations

import functools
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from .api import DEFAULT_API, DEFAULT_TIMEOUT, Api, ApiError
from .tools import Fiskalna

INSTRUCTIONS = (
    "Fiskalna karta JLS: ocjena financijske stabilnosti svih 576 općina, gradova i županija u Hrvatskoj "
    "(1 = ozbiljan pritisak, 5 = vrlo stabilno), iz podataka Ministarstva financija (PR-RAS i Bilanca). "
    "Odgovaraj samo brojkama koje vrate alati i uvijek navedi poveznicu na stranicu jedinice ili izvor. "
    "Ne računaj nove brojke i ne nagađaj. Jedinicu zadaj slugom, nazivom ili šifrom DGU (npr. 05738). "
    "Kad nisi siguran koja je jedinica, prvo pozovi pronadi_jedinicu. "
    "Simulator spajanja i Karta reforme su scenariji, ne prijedlozi granica."
)

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True, open_world_hint=False)

Unit = Annotated[str, Field(description="Slug (npr. opcina-povljana), naziv (npr. Povljana) ili šifra DGU (npr. 05738).")]
Units = Annotated[list[str] | str, Field(
    description="Popis jedinica (slug, naziv ili šifra DGU), kao lista ili jedan tekst odvojen zarezima, npr. \"05738,03166\".")]
Year = Annotated[int | None, Field(description="Godina 2019-2025; zadano je zadnja godina.")]


def _safe(fn):
    """Turn API failures (network, timeout, a file being rewritten) into a message."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ApiError as e:
            return {"greska": str(e)}
    return wrapper


def create_server(api: Api | str | None = None, timeout: float = DEFAULT_TIMEOUT) -> MCPServer:
    if not isinstance(api, Api):
        api = Api(api or DEFAULT_API, timeout=timeout)
    f = Fiskalna(api)
    server = MCPServer("Fiskalna karta", title="Fiskalna karta JLS", instructions=INSTRUCTIONS, version="1.0.0",
                       website_url=api.site)

    @server.tool(annotations=READ_ONLY, description=(
        "Traži jedinicu lokalne ili područne samouprave po nazivu, bez obzira na dijakritike (\"osijek\", "
        "\"povljana\", \"dakovo\"). Vraća slug, naziv, vrstu, županiju, šifru DGU, ocjenu i bodove za zadnju godinu "
        "te poveznicu na pregled jedinice."))
    @_safe
    def pronadi_jedinicu(
        naziv: Annotated[str, Field(description="Naziv ili dio naziva, npr. \"Sveta Nedelja\".")],
        zupanija: Annotated[str | None, Field(description="Po izboru: županija, npr. \"Istarska\".")] = None,
    ) -> dict[str, Any]:
        return f.pronadi_jedinicu(naziv, zupanija)

    @server.tool(annotations=READ_ONLY, description=(
        "Pregled jedinice: ocjena 1-5 i bodovi 0-100, pet sastavnica (I1-I5) s bodovima i medijanom usporedne "
        "skupine, rang u skupini, zastavice upozorenja, kontekst koji ne ulazi u ocjenu (stanovništvo, neto dohodak, "
        "fiskalno izravnanje, revizija DUR-a) i kratko objašnjenje s oznakom AI tekst ili predložak. "
        "Sadrži poveznice na stranicu jedinice i na izvor.json."))
    @_safe
    def pregled_jedinice(jedinica: Unit, godina: Year = None) -> dict[str, Any]:
        return f.pregled_jedinice(jedinica, godina)

    @server.tool(annotations=READ_ONLY, description=(
        "Usporedba 2-5 jedinica jedna uz drugu: ocjena, bodovi, rang i sastavnice I1-I5, uz medijane njihovih "
        "usporednih skupina."))
    @_safe
    def usporedi(jedinice: Units, godina: Year = None) -> dict[str, Any]:
        return f.usporedi(jedinice, godina)

    @server.tool(annotations=READ_ONLY, description=(
        "Simulator spajanja: 2-4 susjedne općine ili grada iste županije (bez županija i Grada Zagreba). "
        "Vraća ocjenu članica prije i spojene jedinice poslije, raspon uštede na općoj upravi, promjenu isplate "
        "fiskalnog izravnanja, poticaj za spajanje i kretanje stanovništva. Za nevaljanu kombinaciju vraća "
        "poruku zašto (druga županija, ne graniče, Zagreb)."))
    @_safe
    def scenarij_spajanja(jedinice: Units) -> dict[str, Any]:
        return f.scenarij_spajanja(jedinice)

    @server.tool(annotations=READ_ONLY, description=(
        "Karta reforme: scenarij u kojem se unutar svake županije spajaju susjedne jedinice dok svaka ne dosegne "
        "prag stanovnika (2500, 5000 ili 10000). Vraća broj jedinica prije i poslije, raspon uštede, poticaj i "
        "preraspodjelu izravnanja; uz zadanu jedinicu i njezinu spojenu skupinu."))
    @_safe
    def karta_reforme(
        prag: Annotated[int, Field(description="Prag stanovnika: 2500, 5000 ili 10000.")] = 5000,
        jedinica: Annotated[str | None, Field(description="Po izboru: jedinica čija se skupina prikazuje.")] = None,
    ) -> dict[str, Any]:
        return f.karta_reforme(prag, jedinica)

    @server.tool(annotations=READ_ONLY, description=(
        "Odakle dolazi brojka: formula pokazatelja, veličine po godinama i svaki ulaz s kontom, iznosom, "
        "datotekom, listom i retkom u izvještajima Ministarstva financija (PR-RAS, Bilanca, odluka o izravnanju)."))
    @_safe
    def izvor_brojke(
        jedinica: Unit,
        pokazatelj: Annotated[str, Field(description=(
            "I1-I5 ili naziv (\"operativni saldo\", \"dospjele obveze\"...), veličina (KP, PO, OS, glavnica, ND, "
            "SD, ZO, FI, DO) ili \"bodovi\"."))] = "I5",
    ) -> dict[str, Any]:
        return f.izvor_brojke(jedinica, pokazatelj)

    @server.resource("fiskalna://metodologija", name="metodologija", title="Metodologija ocjene",
                     description="Pragovi, ponderi, pravila, zastavice i AI postupak (metodologija.json).",
                     mime_type="application/json")
    def metodologija() -> str:
        try:
            return f.metodologija()
        except ApiError as e:
            return '{"greska": %r}' % str(e)

    return server
