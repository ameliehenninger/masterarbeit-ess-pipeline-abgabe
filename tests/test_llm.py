"""Tests für Phase 3 (LLM füllt den Fragebogen aus) – ohne API-Aufrufe, mit einem Fake-Modell."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from ess_pipeline.codebook import parse_variable_texts
from ess_pipeline.config import PVQ_ITEMS, Paths
from ess_pipeline.csv_io import read_ess_csv
from ess_pipeline.llm import experiment as ex
from ess_pipeline.llm.persona import build_persona, load_variable_info
from ess_pipeline.llm.prompts import build_questionnaire, response_schema, system_prompt, user_prompt
from ess_pipeline.llm.providers import Completion
from ess_pipeline.llm.responses import draw_one, parse_response, sample_answers

PATHS = Paths()
KEYS = [f"Q{i}" for i in range(1, 22)]
SCALE = [1, 2, 3, 4, 5, 6]
needs_data = pytest.mark.skipif(not (PATHS.profile_csv.exists() and PATHS.codebook_html.exists()),
                                reason="bereinigte Daten / Codebook fehlen")


def _vs_response(probs=(0.05, 0.15, 0.4, 0.25, 0.1, 0.05)) -> dict:
    return {k: {"reasoning": "Because.", "probabilities": {str(c): p for c, p in zip(SCALE, probs, strict=True)}}
            for k in KEYS}


def _direct_response(answer=3) -> dict:
    return {k: {"answer": answer} for k in KEYS}


def _dump(resp: dict) -> str:
    """{Q1: {...}, …} -> JSON im Antwortformat {"answers": [{"question": "Q1", …}, …]}"""
    return json.dumps({"answers": [{"question": k, **v} for k, v in resp.items()]})


# ---------------------------------------------------------------------------
# Antwortprüfung und Ziehung
# ---------------------------------------------------------------------------

def test_valid_response_is_accepted_and_normalised():
    resp = _vs_response(probs=(0.05, 0.15, 0.4, 0.25, 0.1, 0.06))  # Summe 1.01 -> normiert
    answers, errors = parse_response(_dump(resp), KEYS, SCALE, True, 0.02)
    assert errors == []
    assert sum(answers["Q1"].probabilities) == pytest.approx(1)
    assert answers["Q21"].answer_model is None  # mit Verbalized Sampling wählt das Modell nicht selbst
    assert answers["Q1"].reasoning == "Because."
    assert answers["Q1"].mode(SCALE) == 3


def test_zero_probabilities_are_allowed():
    resp = _vs_response(probs=(0, 0, 1, 0, 0, 0))
    answers, errors = parse_response(_dump(resp), KEYS, SCALE, True, 0.02)
    assert errors == [] and answers["Q1"].probabilities == [0, 0, 1, 0, 0, 0]


@pytest.mark.parametrize("mutate, fragment", [
    (lambda r: r.pop("Q7"), "fehlende Fragen"),
    (lambda r: r["Q1"].pop("probabilities"), "Wahrscheinlichkeiten fehlen"),
    (lambda r: r["Q2"]["probabilities"].update({"1": 0.5}), "Summe"),
    (lambda r: r["Q3"]["probabilities"].update({"1": -0.05, "3": 0.5}), "ungültige"),
    (lambda r: r["Q4"]["probabilities"].update({"1": True}), "ungültige"),
])
def test_invalid_vs_responses_are_rejected(mutate, fragment):
    resp = _vs_response()
    mutate(resp)
    answers, errors = parse_response(_dump(resp), KEYS, SCALE, True, 0.02)
    assert answers is None
    assert any(fragment in e for e in errors), errors


@pytest.mark.parametrize("answer", [7, True, None])
def test_invalid_direct_answers_are_rejected(answer):
    resp = _direct_response()
    resp["Q1"]["answer"] = answer
    answers, errors = parse_response(_dump(resp), KEYS, SCALE, False, 0.02)
    assert answers is None and "nicht in" in errors[0]


def test_direct_answer_is_accepted():
    answers, errors = parse_response(_dump(_direct_response(5)), KEYS, SCALE, False, 0.02)
    assert errors == [] and answers["Q1"].answer_model == 5 and answers["Q1"].probabilities is None


def test_duplicate_question_is_rejected():
    payload = json.loads(_dump(_vs_response()))
    payload["answers"].append(dict(payload["answers"][0]))
    answers, errors = parse_response(json.dumps(payload), KEYS, SCALE, True, 0.02)
    assert answers is None and "doppelt" in errors[0]


def test_not_json_is_rejected():
    answers, errors = parse_response("Sure! Here is my answer", KEYS, SCALE, True, 0.02)
    assert answers is None and "JSON" in errors[0]


def _answers_of(draws):
    return {k: d.answer for k, d in draws.items()}


def test_sampling_is_reproducible_and_follows_distribution():
    answers, _ = parse_response(_dump(_vs_response(probs=(0, 0, 1, 0, 0, 0))), KEYS, SCALE, True, 0.02)
    assert set(_answers_of(sample_answers(answers, KEYS, SCALE, 42, "DE_1")).values()) == {3}
    answers, _ = parse_response(_dump(_vs_response()), KEYS, SCALE, True, 0.02)
    a = sample_answers(answers, KEYS, SCALE, 42, "DE_1")
    assert a == sample_answers(answers, KEYS, SCALE, 42, "DE_1")
    assert (_answers_of(a) != _answers_of(sample_answers(answers, KEYS, SCALE, 42, "DE_2"))
            or _answers_of(a) != _answers_of(sample_answers(answers, KEYS, SCALE, 7, "DE_1")))


@pytest.mark.parametrize("u, expected", [(0.0, 1), (0.0999, 1), (0.1, 2), (0.53, 3), (0.7, 4), (0.95, 5),
                                         (0.99999, 5)])
def test_draw_picks_the_interval_containing_u(u, expected):
    d = draw_one([0.1, 0.2, 0.4, 0.2, 0.1, 0.0], SCALE, u)
    assert d.answer == expected and d.random_number == u
    assert d.upper_bounds == pytest.approx([0.1, 0.3, 0.7, 0.9, 1.0, 1.0])


def test_draw_matches_the_distribution_in_the_long_run():
    import numpy as np
    rng = np.random.default_rng(0)
    p = [0.1, 0.2, 0.4, 0.2, 0.1, 0.0]
    counts = np.bincount([draw_one(p, SCALE, float(rng.random())).answer for _ in range(20000)], minlength=7)[1:]
    assert counts / counts.sum() == pytest.approx(p, abs=0.015)


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def data():
    info = load_variable_info(PATHS.missing_codes_csv, PATHS.codebook_html)
    q = build_questionnaire(PVQ_ORDER(), parse_variable_texts(PATHS.codebook_html), info["ipcrtiva"].labels)
    return info, q, read_ess_csv(PATHS.profile_csv).df


def PVQ_ORDER() -> list[str]:
    return [c for c in read_ess_csv(PATHS.questionnaire_csv).df.columns if c != "id"]


@needs_data
def test_prompt_contains_no_id_and_all_items(data):
    info, q, profile = data
    row = profile.iloc[0].to_dict()
    persona = build_persona(row, info, ["id", "idno"])
    text = system_prompt(persona.text, True, True) + user_prompt(q)
    assert row["id"] not in text and f" {row['idno']} " not in text
    assert all(f"Q{i}. " in text for i in range(1, 22))
    assert not any(item in text for item in PVQ_ITEMS)  # keine ESS-Variablennamen
    assert "-year-old" in persona.text and persona.generic == []


@needs_data
def test_system_prompt_has_only_respondent_context(data):
    info, _, profile = data
    persona = build_persona(profile.iloc[0].to_dict(), info, ex.PromptCfg().exclude_profile_columns)
    system = system_prompt(persona.text, True, True)
    # Reihenfolge: Situation -> Profil -> Anleitung
    assert system.index("interview") < system.index("# Who you are") < system.index("# How to answer")
    # kein Forschungs- oder Modellkontext, keine Codebook-Sprache
    for word in ("mode collapse", "variance collapse", "AI", "language model", "thesis", "study", "ESS",
                 "post-coded", "not applicable", "German classification", "randomised", "test question",
                 "listed in the survey"):
        assert word not in system, word
    # Verbalized Sampling: Überlegung vor der Verteilung, keine eigene Wahl des Modells
    assert system.index("reasoning:") < system.index("probabilities:")
    assert "commit" not in system and "choose the one" not in system
    assert "choose the one answer option" in system_prompt(persona.text, False, False)


@needs_data
def test_every_profile_variable_except_ids_is_verbalised(data):
    info, _, profile = data
    exclude = ex.PromptCfg().exclude_profile_columns
    for row in profile.head(200).to_dict(orient="records"):
        persona = build_persona(row, info, exclude)
        non_empty = {c for c, v in row.items() if c not in exclude and v.strip() != ""}
        assert persona.covered == non_empty, row["id"]
        assert persona.generic == [], (row["id"], persona.generic)
        assert "{" not in persona.text and ".." not in persona.text


@needs_data
def test_schema_requires_all_questions(data):
    _, q, _ = data
    item = response_schema(q, True)["properties"]["answers"]["items"]
    assert item["properties"]["question"]["enum"] == KEYS
    assert list(item["properties"]) == ["question", "reasoning", "probabilities"]  # VS-CoT, keine eigene Wahl
    direct = response_schema(q, False)["properties"]["answers"]["items"]
    assert list(direct["properties"]) == ["question", "answer"]
    assert direct["properties"]["answer"]["enum"] == SCALE


# ---------------------------------------------------------------------------
# Kompletter Lauf mit Fake-Modell
# ---------------------------------------------------------------------------

class FakeProvider:
    name = "fake"

    def __init__(self, bad_first: bool = False):
        self.calls = 0
        self.bad_first = bad_first

    def request_params(self):
        return {"provider": "fake"}

    def complete(self, system, user, schema):
        self.calls += 1
        if self.bad_first and self.calls == 1:
            return Completion("{}", "end_turn")
        # ganze Masse auf Option 3 -> die extern gezogene Antwort muss 3 sein
        text = _dump(_vs_response(probs=(0, 0, 1, 0, 0, 0)))
        return Completion(text, "end_turn", {"input_tokens": 100, "output_tokens": 50},
                          thinking=["Thinking about the person."], raw={"content": [{"type": "text", "text": text}]})


@needs_data
def test_full_run_with_fake_model(tmp_path, monkeypatch):
    (tmp_path / "data").symlink_to(PATHS.root / "data")
    paths = Paths(tmp_path)
    fake = FakeProvider(bad_first=True)
    monkeypatch.setattr(ex, "make_provider", lambda *a, **k: fake)
    cfg = ex.ExperimentConfig(run_name="test")
    cfg.run.parallel_requests = 1

    results = ex.run_fill(cfg, paths)
    out = paths.results_dir / "llm" / "test"
    assert [r.ok for r in results] == [True, True]
    assert results[0].attempts == 2  # erster Versuch ungültig -> wiederholt

    llm = read_ess_csv(out / ex.QUESTIONNAIRE_CSV)
    human = read_ess_csv(PATHS.questionnaire_csv)
    assert list(llm.df.columns) == list(human.df.columns)
    assert llm.text_columns == {"id"}
    assert list(llm.df["id"]) == list(human.df["id"][:2])
    assert set(llm.df[PVQ_ITEMS].stack()) == {"3"}
    detail = pd.read_csv(out / ex.DETAIL_CSV)
    assert "antwort_modell" not in detail and set(detail["modus"]) == {3}
    pid = llm.df["id"][0]
    assert (out / "prompts" / f"{pid}.txt").exists()
    entry = json.loads((out / "logs" / f"{pid}.json").read_text())
    assert entry["status"] == "ok" and len(entry["attempts"]) == 2
    # alle Zwischenschritte im Log: Denk-Zusammenfassung, komplette API-Antwort, Verteilung, Ziehung
    last = entry["attempts"][-1]
    assert last["thinking"] == ["Thinking about the person."] and last["response_raw"]["content"]
    q1 = entry["answers"]["Q1"]
    assert q1["item"] == PVQ_ITEMS[0] or q1["item"] in PVQ_ITEMS
    assert q1["probabilities_raw"] == [0, 0, 1, 0, 0, 0] and q1["upper_bounds"] == [0, 0, 1, 1, 1, 1]
    assert 0 <= q1["random_number"] < 1 and q1["answer_final"] == 3
    assert entry["sampling"]["sampling_seed"] == 42
    trace = (out / "traces" / f"{pid}.md").read_text()
    assert "Thinking about the person." in trace and "Zufallszahl u =" in trace and "finale Antwort 3" in trace
    assert {"zufallszahl", "p_roh1", "grenze6", "fragetext", "begruendung"} <= set(detail.columns)
    assert "FEHLER" not in (out / ex.REPORT_MD).read_text()

    # zweiter Lauf: alles aus den Logs, kein neuer Aufruf
    calls = fake.calls
    assert all(r.reused for r in ex.run_fill(cfg, paths))
    assert fake.calls == calls
    pd.testing.assert_frame_equal(read_ess_csv(out / ex.QUESTIONNAIRE_CSV).df, llm.df)


@needs_data
def test_full_run_batch_mode(tmp_path, monkeypatch):
    """Batch-Modus: ungültige Antwort und Batch-Fehler landen in einer zweiten Runde (= neuer Batch)."""
    from ess_pipeline.llm import batch as batch_mod

    (tmp_path / "data").symlink_to(PATHS.root / "data")
    paths = Paths(tmp_path)
    fake = FakeProvider()
    fake.message_params = lambda system, user, schema: {"system": system}
    monkeypatch.setattr(ex, "make_provider", lambda *a, **k: fake)
    rounds = []

    def fake_run_batch(provider, params, out, poll_s):
        rounds.append(sorted(params))
        ids = sorted(params)
        out = batch_mod.BatchOutcome(f"batch_{len(rounds)}", 1.5)
        for i, pid in enumerate(ids):
            if len(rounds) == 1 and i == 0:
                out.completions[pid] = Completion("{}", "end_turn")      # ungültig
            elif len(rounds) == 1 and i == 1:
                out.errors[pid] = "Batch-Ergebnis 'expired'"            # keine Antwort
            else:
                out.completions[pid] = fake.complete(None, None, None)
        return out

    monkeypatch.setattr(batch_mod, "run_batch", fake_run_batch)
    cfg = ex.ExperimentConfig(run_name="test_batch")
    cfg.run.mode = "batch"

    results = ex.run_fill(cfg, paths)
    assert [r.ok for r in results] == [True, True] and [r.attempts for r in results] == [2, 2]
    assert len(rounds) == 2 and rounds[0] == rounds[1]
    pid = results[0].id
    entry = json.loads((paths.results_dir / "llm" / "test_batch" / "logs" / f"{pid}.json").read_text())
    assert entry["request"]["mode"] == "batch"
    assert [a["batch_id"] for a in entry["attempts"]] == ["batch_1", "batch_2"]
    assert entry["attempts"][-1]["usage"] == {"input_tokens": 100, "output_tokens": 50}


def test_config_rejects_unknown_keys(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("persons:\n  nn: 3\n")
    with pytest.raises(ValueError, match="nn"):
        ex.load_config(p)


def test_repository_config_loads():
    """Hauptexperiment: alle Personen, Haiku, Batch; Ergebnisordner wie im Repository."""
    cfg = ex.load_config(PATHS.root / "config" / "llm_experiment.yaml")
    assert cfg.persons.n is None and cfg.model.name == "claude-haiku-5-5" and cfg.run.mode == "batch"
    assert "id" in cfg.prompt.exclude_profile_columns and "idno" in cfg.prompt.exclude_profile_columns
    assert ex.out_dir(PATHS, cfg).is_dir()


def test_vorexperiment_configs_load():
    configs = sorted((PATHS.root / "config" / "vorexperiment_which_thinking_mode").glob("*.yaml"))
    assert len(configs) == 6
    for path in configs:
        cfg = ex.load_config(path)
        assert cfg.run_name.startswith("vorexperiment_which_thinking_mode/")
        assert ex.out_dir(PATHS, cfg).is_dir(), path.name


# ---------------------------------------------------------------------------
# Verteilungsanalyse und Batch-Protokoll
# ---------------------------------------------------------------------------

def test_distribution_measures():
    from ess_pipeline.llm import distributions as dist

    uniform = np.full(6, 1 / 6)
    onehot = np.array([0, 0, 1, 0, 0, 0], float)
    assert dist.entropy_bits(uniform) == pytest.approx(np.log2(6))
    assert dist.entropy_bits(onehot) == pytest.approx(0)
    assert dist.js_divergence(uniform, uniform) == pytest.approx(0)
    assert dist.js_divergence(onehot, np.array([1, 0, 0, 0, 0, 0], float)) == pytest.approx(1)
    assert dist.wasserstein(onehot, np.array([1, 0, 0, 0, 0, 0], float)) == pytest.approx(2)
    assert dist.is_unimodal(np.array([0.1, 0.3, 0.3, 0.2, 0.1, 0]))
    assert not dist.is_unimodal(np.array([0.4, 0.1, 0.0, 0.1, 0.4, 0]))
    assert list(dist.histogram(np.array([1, 1, 6, 7, 77, np.nan]))) == [2 / 3, 0, 0, 0, 0, 1 / 3]


def test_batch_log_resumes_open_batch(tmp_path):
    from ess_pipeline.llm import batch as b

    params = {"DE_1": {"model": "m", "system": "s"}}
    key = b._key(params)
    assert b._open_batch(tmp_path, key) is None
    b._append(tmp_path, {"event": "submitted", "batch_id": "msgbatch_a", "key": key})
    assert b._open_batch(tmp_path, key) == "msgbatch_a"
    assert b._open_batch(tmp_path, b._key({"DE_2": {}})) is None   # andere Anfragen -> neuer Batch
    b._append(tmp_path, {"event": "collected", "batch_id": "msgbatch_a"})
    assert b._open_batch(tmp_path, key) is None
