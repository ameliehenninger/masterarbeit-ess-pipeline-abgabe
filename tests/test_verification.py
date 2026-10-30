"""
Unabhängige Verifikation von results/mensch/ess_scores.csv mit exakten Brüchen
(siehe DOKUMENTATION.md, Abschnitt 3.4). Nutzt bewusst keinen Pipeline-Code.
"""

from __future__ import annotations

import csv
from fractions import Fraction as F

import pytest

from ess_pipeline.config import Paths

MAP = {
    "SD": ["ipcrtiva", "impfreea"], "ST": ["impdiffa", "ipadvnta"], "HE": ["ipgdtima", "impfuna"],
    "AC": ["ipshabta", "ipsucesa"], "PO": ["impricha", "iprspota"], "SE": ["impsafea", "ipstrgva"],
    "CO": ["ipfrulea", "ipbhprpa"], "TR": ["ipmodsta", "imptrada"], "BE": ["iphlppla", "iplylfra"],
    "UN": ["ipeqopta", "ipudrsta", "impenva"],
}
HO = {"OPEN": ["SD", "ST", "HE"], "CONS": ["SE", "CO", "TR"], "SELFENH": ["AC", "PO"], "SELFTRANS": ["UN", "BE"]}

PATHS = Paths()
pytestmark = pytest.mark.skipif(not (PATHS.questionnaire_csv.exists() and PATHS.scores_csv.exists()),
                                reason="Fragebogen/Scores nicht vorhanden")


def exact_scores(row: dict[str, str]) -> dict[str, F]:
    rev = {i: 7 - int(row[i]) for items in MAP.values() for i in items}
    mrat = F(sum(rev.values()), len(rev))
    out = {"MRAT": mrat}
    for bv, items in MAP.items():
        out[bv] = F(sum(rev[i] for i in items), len(items)) - mrat
    for ho, bvs in HO.items():
        out[ho] = sum(out[bv] for bv in bvs) / len(bvs)
    out["x"] = out["SELFTRANS"] - out["SELFENH"]
    out["y"] = out["OPEN"] - out["CONS"]
    return out


def _read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def test_all_persons_match_exact_recalculation():
    quest, scores = _read(PATHS.questionnaire_csv), _read(PATHS.scores_csv)
    assert list(quest) == list(scores)
    for pid, row in quest.items():
        e = exact_scores(row)
        # Zentrierung: gewichtete Summe der Basiswerte ist exakt 0
        assert sum(len(MAP[bv]) * e[bv] for bv in MAP) == 0
        # Higher-Order: gleichwertig über die gepoolten Items (gleich viele Items je Basiswert)
        rev = {i: 7 - int(row[i]) for items in MAP.values() for i in items}
        for ho in ("OPEN", "CONS", "SELFENH"):
            items = [i for bv in HO[ho] for i in MAP[bv]]
            assert e[ho] == F(sum(rev[i] for i in items), len(items)) - e["MRAT"]
        # SELFTRANS: UN hat 3 Items, BE 2 -> Mittel der Basiswerte, nicht der 5 Items
        assert e["SELFTRANS"] == (e["UN"] + e["BE"]) / 2
        for col, v in e.items():
            assert float(scores[pid][col]) == pytest.approx(float(v), abs=1e-12), (pid, col)


def test_worked_example_de_50032():
    e = exact_scores(_read(PATHS.questionnaire_csv)["DE_50032"])
    expected = {
        "MRAT": F(86, 21), "SD": F(59, 42), "ST": F(17, 42), "HE": F(17, 42), "AC": F(-23, 21),
        "PO": F(-25, 42), "SE": F(-25, 42), "CO": F(-67, 42), "TR": F(-23, 21), "BE": F(59, 42),
        "UN": F(19, 21), "OPEN": F(31, 42), "CONS": F(-23, 21), "SELFENH": F(-71, 84),
        "SELFTRANS": F(97, 84), "x": F(2), "y": F(11, 6),
    }
    assert e == expected
