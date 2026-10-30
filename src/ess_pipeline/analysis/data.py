"""
Daten für die Auswertung: echte Antworten, LLM-Antworten und Demografie, nach Personen-ID ausgerichtet.

Alle Items werden umgepolt (x' = 7 − x), damit 6 = „sehr wichtig“ und 1 = „gar nicht wichtig“ bedeutet.
Ein positiver Fehler (LLM − Mensch) heißt damit: Das LLM schreibt dem Wert mehr Wichtigkeit zu als der Mensch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ESS_ITEM_MAP, ID_COL, PVQ_ITEMS

BASIC_VALUES = list(ESS_ITEM_MAP)
ITEM_VALUE = {item: value for value, items in ESS_ITEM_MAP.items() for item in items}

# Subgruppen für Ebene 1: Anzeigename -> (Spalte im Profil, Funktion Rohwert-Serie -> Gruppenlabel)
EAST = {"DE3", "DE4", "DE8", "DED", "DEE", "DEG"}   # Berlin, Brandenburg, MV, Sachsen, Sachsen-Anhalt, Thüringen


def _age(s: pd.Series) -> pd.Series:
    a = pd.to_numeric(s, errors="coerce")
    return pd.cut(a, [14, 29, 44, 59, 74, 120], labels=["15–29", "30–44", "45–59", "60–74", "75+"]).astype(object)


def _map(mapping: dict[str, str]):
    return lambda s: s.map(mapping)


SUBGROUPS: dict[str, tuple[str, callable]] = {
    "Geschlecht": ("gndr", _map({"1": "männlich", "2": "weiblich"})),
    "Alter": ("agea", _age),
    "Schulabschluss": ("edudde1", _map({"1": "niedrig", "2": "niedrig", "3": "mittel", "4": "hoch", "5": "hoch"})),
    "Wohnort": ("domicil", _map({"1": "Großstadt", "2": "Großstadt", "3": "Kleinstadt", "4": "ländlich",
                                 "5": "ländlich"})),
    "Region": ("region", lambda s: s.where(s == "", s.isin(EAST).map({True: "Ost", False: "West"}))),
    "Religion": ("rlgblg", _map({"1": "religiös gebunden", "2": "nicht gebunden"})),
}
SUBGROUP_NOTES = {
    "Schulabschluss": "niedrig = kein Abschluss/Hauptschule, mittel = Realschule, hoch = Fach-/Hochschulreife",
    "Wohnort": "Großstadt inkl. Vororte; ländlich = Dorf oder Einzelhof",
    "Region": "Ost = neue Bundesländer inkl. Berlin",
}


@dataclass
class Twins:
    ids: list[str]
    human: pd.DataFrame        # Index id, Spalten PVQ_ITEMS, umgepolt (1–6)
    llm: pd.DataFrame
    human_scores: pd.DataFrame  # Index id, Spalten wie scores-CSV (SD … UN, OPEN …, x, y)
    llm_scores: pd.DataFrame
    demo: pd.DataFrame          # Index id, eine Spalte je Subgruppen-Merkmal (Label oder NaN)
    question_no: dict[str, int]  # item -> Position im Fragebogen (Q1 … Q21)
    population_mean: np.ndarray | None = None  # mittlere Antwort je Item über ALLE echten Personen

    def items(self, who: str) -> np.ndarray:
        return (self.human if who == "human" else self.llm).to_numpy(float)


def _items(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={ID_COL: str}).set_index(ID_COL)[PVQ_ITEMS].apply(pd.to_numeric, errors="coerce")
    return 7 - df


def demographics(profile_csv: Path) -> pd.DataFrame:
    prof = pd.read_csv(profile_csv, dtype=str, keep_default_na=False).set_index(ID_COL)
    out = pd.DataFrame(index=prof.index)
    for name, (col, fn) in SUBGROUPS.items():
        out[name] = fn(prof[col]).replace("", np.nan)
    return out


def load_twins(run_dir: Path, questionnaire_csv: Path, human_scores_csv: Path, profile_csv: Path,
               questionnaire_name: str = "fragebogen_LLM.csv", scores_name: str = "scores_LLM.csv") -> Twins:
    """Nur Personen, für die beide Fragebögen vollständig vorliegen (Reihenfolge wie im LLM-Lauf)."""
    llm = _items(run_dir / questionnaire_name)
    human = _items(questionnaire_csv)
    ids = [i for i in llm.index if i in human.index]
    ok = human.loc[ids].notna().all(axis=1) & llm.loc[ids].notna().all(axis=1)
    ids = [i for i in ids if ok[i]]
    hs = pd.read_csv(human_scores_csv, dtype={ID_COL: str}).set_index(ID_COL).loc[ids]
    ls = pd.read_csv(run_dir / scores_name, dtype={ID_COL: str}).set_index(ID_COL).loc[ids]
    order = [c for c in pd.read_csv(questionnaire_csv, nrows=0).columns if c in PVQ_ITEMS]
    return Twins(ids, human.loc[ids], llm.loc[ids], hs, ls, demographics(profile_csv).reindex(ids),
                 {item: i + 1 for i, item in enumerate(order)}, human.dropna().mean().to_numpy(float))
