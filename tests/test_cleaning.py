"""Unit-Tests der Bereinigungsschritte mit kleinen, synthetischen Daten."""

from __future__ import annotations

import pandas as pd
import pytest

from ess_pipeline import cleaning as cl
from ess_pipeline.codebook import missing_codes, parse_codebook
from ess_pipeline.config import ID_COL, PROFILE_DROP_COLUMNS, PVQ_ITEMS
from ess_pipeline.csv_io import Table, read_ess_csv, write_ess_csv

ITEMS = ["i1", "i2"]


def make_raw() -> Table:
    df = pd.DataFrame({
        "name": ["ESS", "ESS", "ESS", "ESS"],
        "idno": ["1", "2", "3", "4"],
        "cntry": ["DE", "DE", "AT", "DE"],
        "i1": ["1", "77", "2", "3"],
        "i2": ["2", "3", "4", ""],
        "empty": ["", "", " ", ""],
        "flag": ["0", "0", "0", "1"],
        "income": ["5", "99", "0", "7"],
    })
    return Table(df, {"name", "cntry"})


def test_split_builds_id_and_keeps_column_order():
    profile, quest = cl.split_profile_questionnaire(make_raw(), ITEMS)
    assert quest.df.columns.tolist() == ["id", "i1", "i2"]
    assert profile.df.columns.tolist() == ["id", "name", "idno", "cntry", "empty", "flag", "income"]
    assert profile.df["id"].tolist() == ["DE_1", "DE_2", "AT_3", "DE_4"]
    assert "id" in profile.text_columns and "id" in quest.text_columns


def test_split_rejects_duplicate_ids():
    raw = make_raw()
    raw.df.loc[1, "idno"] = "1"
    with pytest.raises(ValueError, match="Doppelte IDs"):
        cl.split_profile_questionnaire(raw, ITEMS)


def test_incomplete_and_country_filter_match_by_id():
    profile, quest = cl.split_profile_questionnaire(make_raw(), ITEMS)
    complete = cl.complete_questionnaire_ids(quest, ITEMS)
    assert complete.tolist() == ["DE_1", "DE_2", "AT_3"]  # "77" ist noch kein Leerwert
    profile, quest = cl.keep_persons(profile, quest, complete)
    profile, quest = cl.keep_persons(profile, quest, cl.country_ids(profile, "DE"))
    assert profile.df["id"].tolist() == quest.df["id"].tolist() == ["DE_1", "DE_2"]


def test_empty_and_mostly_zero_columns():
    profile, _ = cl.split_profile_questionnaire(make_raw(), ITEMS)
    assert cl.empty_columns(profile) == ["empty"]          # " " zählt als leer
    assert cl.mostly_zero_columns(profile, 0.5) == ["flag"]  # 3/4 > 50 %
    assert cl.mostly_zero_columns(profile, 0.75) == []       # strikt größer


def test_drop_columns_protects_id_and_items():
    profile, _ = cl.split_profile_questionnaire(make_raw(), ITEMS)
    with pytest.raises(ValueError, match="Geschützte"):
        cl.drop_columns(profile, ["id"], protected={"id"})


def test_step8_drop_list_keeps_id_items_and_weights():
    drop = set(PROFILE_DROP_COLUMNS)
    assert len(drop) == len(PROFILE_DROP_COLUMNS)  # keine Doppelungen
    keep = {ID_COL, "idno", "cntry", "gndr", "agea", "edudde1", "educde2", *PVQ_ITEMS,
            "dweight", "pspwght", "pweight", "anweight", "domain", "prob", "stratum", "psu"}
    assert not drop & keep


def test_blank_missing_codes_only_per_variable():
    _, quest = cl.split_profile_questionnaire(make_raw(), ITEMS)
    out, n = cl.blank_missing_codes(quest, {"i1": {"77"}, "i2": {"99"}})
    assert n == 1
    assert out.df["i1"].tolist() == ["1", "", "2", "3"]
    assert out.df["i2"].tolist() == ["2", "3", "4", ""]


def test_codebook_parser_marks_asterisk_as_missing(tmp_path):
    html = """
    <h3 id="ipcrtiva">ipcrtiva</h3>
    <table><tbody class="codelist">
      <tr><td class="nowrap">1</td><td>Very much like me</td></tr>
      <tr><td class="nowrap">77</td><td>Refusal*</td></tr>
    </tbody></table>
    <h3 id="idno">idno</h3>
    """
    path = tmp_path / "cb.html"
    path.write_text(html, encoding="utf-8")
    cb = parse_codebook(path)
    assert cb.to_dict("records") == [
        {"variable": "ipcrtiva", "code": "1", "label": "Very much like me", "is_missing": False},
        {"variable": "ipcrtiva", "code": "77", "label": "Refusal", "is_missing": True},
    ]
    assert missing_codes(cb) == {"ipcrtiva": {"77"}}


def test_csv_roundtrip_keeps_ess_quoting(tmp_path):
    src = tmp_path / "in.csv"
    content = '"id","name","n","edition"\n"DE_1","ESS",11,"4.2"\n"DE_2",,0.5,""\n'
    src.write_text(content, encoding="utf-8")
    table = read_ess_csv(src)
    assert table.text_columns == {"id", "name", "edition"}
    assert table.df["n"].tolist() == ["11", "0.5"]  # keine float-Umwandlung
    dst = tmp_path / "out.csv"
    write_ess_csv(table, dst)
    # leere Textfelder werden ohne Anführungszeichen geschrieben (wie im Original-Ablauf)
    assert dst.read_text(encoding="utf-8") == '"id","name","n","edition"\n"DE_1","ESS",11,"4.2"\n"DE_2",,0.5,\n'
