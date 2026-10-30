"""
Lesen und Schreiben von CSV-Dateien im Format des ESS-Exports.

Der ESS-Export (Stata-Stil) setzt Textspalten in Anführungszeichen und lässt
Zahlenspalten ohne. Damit Zahlen nicht als float umformatiert werden
(z. B. "11" -> "11.0") und die Ausgabe byte-identisch zum Format des
Originals bleibt, wird alles als Text gelesen und die Textspalten werden
beim Schreiben wieder gequotet.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class Table:
    """DataFrame (nur Strings, leere Zelle = "") plus Menge der Textspalten."""

    df: pd.DataFrame
    text_columns: set[str]

    def subset(self, rows=None, columns: list[str] | None = None) -> Table:
        df = self.df if rows is None else self.df.loc[rows]
        if columns is not None:
            df = df[columns]
        df = df.reset_index(drop=True)
        return Table(df, {c for c in self.text_columns if c in df.columns})


def _unquote(value: str) -> str:
    return value[1:-1].replace('""', '"')


def read_ess_csv(path: str | Path) -> Table:
    """
    Liest eine ESS-CSV als reinen Text und merkt sich, welche Spalten gequotet sind.

    Eingelesen wird mit QUOTE_NONE, damit erkennbar bleibt, welche Felder in
    Anführungszeichen standen. Enthält ein gequotetes Feld ein Komma, bricht
    pandas mit einem Spaltenzahl-Fehler ab (statt still falsch zu lesen).
    """
    raw = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[],
                      quoting=csv.QUOTE_NONE, low_memory=False)
    raw.columns = [_unquote(c) if c.startswith('"') else c for c in raw.columns]

    text_columns: set[str] = set()
    for col in raw.columns:
        s = raw[col]
        quoted = s.str.startswith('"') & s.str.endswith('"') & (s.str.len() >= 2)
        if quoted.any():
            unquoted_values = s[~quoted & (s != "")]
            if not unquoted_values.empty:
                raise ValueError(f"Spalte {col!r} mischt gequotete und ungequotete Werte")
            raw[col] = s.where(~quoted, s.str[1:-1].str.replace('""', '"', regex=False))
            if (raw[col] != "").any():
                text_columns.add(col)
    return Table(raw, text_columns)


def write_ess_csv(table: Table, path: str | Path) -> None:
    """Schreibt im ESS-Format: Header gequotet, nicht-leere Werte in Textspalten gequotet."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    def q(v: str) -> str:
        return '"' + v.replace('"', '""') + '"'

    quote_col = [c in table.text_columns for c in table.df.columns]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(",".join(q(c) for c in table.df.columns) + "\n")
        for row in table.df.itertuples(index=False, name=None):
            f.write(",".join(q(v) if (qc and v != "") else v for v, qc in zip(row, quote_col, strict=True)) + "\n")


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
