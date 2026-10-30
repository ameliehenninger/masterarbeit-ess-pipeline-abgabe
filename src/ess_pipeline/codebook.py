"""
Missing-Codes aus der ESS-11-Dokumentation (HTML-Codebook) ableiten.

Im Codebook ist jede Variable ein <h3 id="variable">-Abschnitt mit einer
Tabelle <tbody class="codelist">. Codes, deren Label mit "*" endet, sind laut
Fußnote "*) Missing value" (z. B. 66 Not applicable, 77 Refusal,
88 Don't know, 99 No answer).
"""

from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

import pandas as pd


class _CodebookParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.codes: dict[str, list[tuple[str, str]]] = {}
        self._var: str | None = None
        self._in_codelist = False
        self._row: list[str] | None = None
        self._cell: str | None = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h3" and "id" in attrs:
            self._var = attrs["id"]
            self.codes[self._var] = []
        elif tag == "tbody" and attrs.get("class") == "codelist":
            self._in_codelist = True
        elif self._in_codelist and tag == "tr":
            self._row = []
        elif self._in_codelist and tag == "td":
            self._cell = ""

    def handle_endtag(self, tag):
        if tag == "tbody":
            self._in_codelist = False
        elif self._in_codelist and tag == "td" and self._row is not None:
            self._row.append((self._cell or "").strip())
            self._cell = None
        elif self._in_codelist and tag == "tr" and self._row is not None:
            if len(self._row) >= 2:
                self.codes[self._var].append((self._row[0], self._row[1]))
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell += data


def parse_codebook(path: str | Path) -> pd.DataFrame:
    """Alle Codelisten als Tabelle: variable, code, label, is_missing."""
    parser = _CodebookParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    rows = [
        {"variable": var, "code": code, "label": label.rstrip("*").strip(),
         "is_missing": label.endswith("*")}
        for var, codes in parser.codes.items()
        for code, label in codes
    ]
    if not rows:
        raise ValueError(f"Keine Codelisten in {path} gefunden – Format geändert?")
    return pd.DataFrame(rows, columns=["variable", "code", "label", "is_missing"])


def missing_codes(codebook: pd.DataFrame) -> dict[str, set[str]]:
    """variable -> Menge der Missing-Codes (als Text, wie in der CSV)."""
    m = codebook[codebook["is_missing"]]
    return m.groupby("variable")["code"].apply(set).to_dict()


def parse_variable_texts(path: str | Path) -> dict[str, list[str]]:
    """
    variable -> Textzeilen vor der Codeliste: [Titel, Kartenhinweis/Fragetext, ...].

    Beispiel ipcrtiva: ["Important to think new ideas and being creative",
    "Now I will briefly describe some people. ... Thinking up new ideas ..."].
    """
    text = Path(path).read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for block in re.split(r'<h3 id="', text)[1:]:
        var = block.split('"', 1)[0]
        body = block.split("</h3>", 1)[1].split('<div class="data-table"', 1)[0].split("<tbody", 1)[0]
        divs = re.findall(r"<div[^>]*>(.*?)</div>", body, re.S)
        lines = [html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", d))).strip() for d in divs]
        out[var] = [s for s in lines if s]
    if not out:
        raise ValueError(f"Keine Variablen in {path} gefunden – Format geändert?")
    return out
