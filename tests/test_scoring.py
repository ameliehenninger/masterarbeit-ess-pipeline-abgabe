"""Unit-Tests der Score-Berechnung mit synthetischen Personen (unabhängig von den ESS-Daten)."""

from __future__ import annotations

from fractions import Fraction as F

import pandas as pd
import pytest

from ess_pipeline import scoring as sc
from ess_pipeline.config import PVQ_ITEMS

HAND_PERSON = {
    "ipcrtiva": 1, "impfreea": 1, "impdiffa": 2, "ipadvnta": 2, "ipgdtima": 3, "impfuna": 3,
    "ipshabta": 4, "ipsucesa": 4, "impricha": 6, "iprspota": 6, "impsafea": 2, "ipstrgva": 2,
    "ipfrulea": 3, "ipbhprpa": 3, "ipmodsta": 5, "imptrada": 5, "iphlppla": 1, "iplylfra": 1,
    "ipeqopta": 1, "ipudrsta": 1, "impenva": 4,
}


@pytest.mark.parametrize("v", range(1, 7))
def test_constant_answers_give_zero_scores(v):
    df = pd.DataFrame([{"id": "C", **{i: v for i in PVQ_ITEMS}}])
    r = sc.compute_scores(df).iloc[0]
    assert r.MRAT == pytest.approx(7 - v)
    for col in sc.SCORE_COLUMNS[1:]:
        assert r[col] == pytest.approx(0, abs=1e-12)


def test_hand_calculated_person():
    r = sc.compute_scores(pd.DataFrame([{"id": "H", **HAND_PERSON}])).iloc[0]
    m = F(29, 7)
    expected = {"MRAT": m, "SD": 6 - m, "PO": 1 - m, "OPEN": F(6, 7), "CONS": F(-10, 21),
                "SELFENH": F(-15, 7), "SELFTRANS": F(19, 14), "x": F(7, 2), "y": F(4, 3)}
    for col, e in expected.items():
        assert r[col] == pytest.approx(float(e), abs=1e-12), col


def test_id_is_kept_as_string_and_order_preserved():
    df = pd.DataFrame([{"id": "007", **HAND_PERSON}, {"id": "001", **HAND_PERSON}]).astype(str)
    out = sc.compute_scores(df)
    assert out["id"].tolist() == ["007", "001"]


@pytest.mark.parametrize("bad", ["0", "7", "2.5", ""])
def test_invalid_values_raise_with_id(bad):
    df = pd.DataFrame([{"id": "X1", **HAND_PERSON}]).astype(str)
    df.loc[0, "impenva"] = bad
    with pytest.raises(sc.InputValidationError, match="X1"):
        sc.compute_scores(df)


def test_missing_item_column_raises():
    df = pd.DataFrame([{"id": "X1", **HAND_PERSON}]).drop(columns=["impfuna"])
    with pytest.raises(sc.InputValidationError, match="impfuna"):
        sc.compute_scores(df)


@pytest.mark.parametrize("option, n_open, n_enh", [("openness", 6, 4), ("both", 6, 6), ("none", 4, 4)])
def test_hedonism_options(option, n_open, n_enh):
    ho = sc.higher_order_items(sc.ESS_ITEM_MAP, option)
    assert len(ho["OPEN"]) == n_open and len(ho["SELFENH"]) == n_enh


def test_invalid_hedonism_option():
    with pytest.raises(ValueError):
        sc.higher_order_basic_values("foo")
