"""
Phase 3 – Experiment: ein LLM füllt den PVQ-21 in der Rolle von ESS-Personen aus.

Ablauf je Person (neuer, leerer Chat):
  1. Profilzeile -> narratives Profil (ohne ID-Spalten)  -> System-Prompt
  2. leerer PVQ-21 (englischer Codebook-Wortlaut)         -> User-Prompt
  3. Modellaufruf mit erzwungenem JSON-Schema, Antwort prüfen, bei Fehler neuer Versuch
  4. finale Antwort je Item: mit Verbalized Sampling extern aus der verbalisierten Verteilung gezogen,
     sonst die Antwort des Modells
  5. alle Zwischenschritte speichern:
       prompts/<id>.txt  System- und User-Prompt
       logs/<id>.json    Anfrage, je Versuch die komplette API-Antwort (inkl. Denk-Zusammenfassung),
                         Prüfergebnis, je Frage Überlegung, Wahrscheinlichkeiten (wie angegeben und normiert),
                         Intervallgrenzen, Zufallszahl und finale Antwort
       traces/<id>.md    dasselbe lesbar aufbereitet: Schritt für Schritt vom Prompt bis zur gezogenen Antwort

Danach: fragebogen_LLM.csv (Format wie ESS_fragebogen_DE.csv), scores_LLM.csv, Abbildungen,
run_report.md. Alle Stellschrauben stehen in config/llm_experiment.yaml.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..codebook import parse_variable_texts
from ..config import ID_COL, Paths
from ..csv_io import Table, read_ess_csv, write_ess_csv
from .persona import Persona, build_persona, load_variable_info
from .prompts import Questionnaire, build_questionnaire, response_schema, system_prompt, user_prompt
from .providers import Completion, Provider, make_provider
from .responses import Draw, ItemAnswer, parse_response, sample_answers

log = logging.getLogger("ess_pipeline.llm")

QUESTIONNAIRE_CSV = "fragebogen_LLM.csv"
DETAIL_CSV = "antworten_LLM_detail.csv"
SAMPLING_RULE = ("je Frage Zufallszahl u aus [0, 1) mit numpy.random.default_rng([sampling_seed, crc32(id)]), "
                 "Fragen in Reihenfolge Q1–Q21; gewählt wird die Option, in deren Intervall "
                 "[obere Grenze der vorigen Option, eigene obere Grenze) u fällt")
SCORES_CSV = "scores_LLM.csv"
REPORT_MD = "run_report.md"


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

@dataclass
class PersonsCfg:
    n: int | None = 2
    selection: str = "first"
    seed: int = 42


@dataclass
class ModelCfg:
    provider: str = "anthropic"
    name: str = "claude-haiku-5-5"
    max_tokens: int = 16000
    effort: str | None = "medium"
    thinking: str = "adaptive"  # adaptive | disabled
    price_per_mtok: dict = field(default_factory=lambda: {"input": 0.10, "output": 0.50})


@dataclass
class PromptCfg:
    anti_collapse_instruction: bool = True
    verbalized_sampling: bool = True
    exclude_profile_columns: list[str] = field(default_factory=lambda: [
        "id", "idno", "dweight", "pspwght", "pweight", "anweight", "domain", "prob", "stratum", "psu"])


@dataclass
class AnswerCfg:
    sampling_seed: int = 42
    probability_tolerance: float = 0.02


@dataclass
class RunCfg:
    max_attempts: int = 3
    parallel_requests: int = 4
    reuse_existing: bool = True
    mode: str = "direct"            # direct | batch (Message Batches API, 50 % Rabatt)
    batch_poll_seconds: float = 30


@dataclass
class ExperimentConfig:
    run_name: str | None = None
    persons: PersonsCfg = field(default_factory=PersonsCfg)
    model: ModelCfg = field(default_factory=ModelCfg)
    prompt: PromptCfg = field(default_factory=PromptCfg)
    answer: AnswerCfg = field(default_factory=AnswerCfg)
    run: RunCfg = field(default_factory=RunCfg)

    @property
    def folder(self) -> str:
        return self.run_name or self.model.name

    def validate(self) -> None:
        if self.persons.selection not in ("first", "random"):
            raise ValueError("persons.selection muss 'first' oder 'random' sein")
        if ID_COL not in self.prompt.exclude_profile_columns:
            raise ValueError(f"Die Spalte {ID_COL!r} muss in prompt.exclude_profile_columns stehen")
        if self.run.mode not in ("direct", "batch"):
            raise ValueError("run.mode muss 'direct' oder 'batch' sein")
        if self.run.max_attempts < 1 or self.run.parallel_requests < 1:
            raise ValueError("run.max_attempts und run.parallel_requests müssen >= 1 sein")


def _from_dict(cls, data: dict | None):
    data = data or {}
    known = {f.name: f for f in fields(cls)}
    unknown = set(data) - set(known)
    if unknown:
        raise ValueError(f"Unbekannte Einträge in der Config ({cls.__name__}): {sorted(unknown)}")
    kwargs = {}
    for name, value in data.items():
        default = known[name].default_factory() if callable(known[name].default_factory) else None
        is_section = default is not None and hasattr(default, "__dataclass_fields__")
        kwargs[name] = _from_dict(type(default), value) if is_section else value
    return cls(**kwargs)


def load_config(path: str | Path) -> ExperimentConfig:
    cfg = _from_dict(ExperimentConfig, yaml.safe_load(Path(path).read_text(encoding="utf-8")))
    cfg.validate()
    return cfg


# ---------------------------------------------------------------------------
# Eine Person
# ---------------------------------------------------------------------------

@dataclass
class PersonResult:
    id: str
    ok: bool
    answers: dict[str, ItemAnswer] | None = None   # Schlüssel Q1…
    draws: dict[str, Draw] | None = None   # nur mit Verbalized Sampling
    attempts: int = 0
    reused: bool = False
    errors: list[str] = field(default_factory=list)
    usage: dict = field(default_factory=dict)
    leak: bool = False
    generic_vars: list[str] = field(default_factory=list)
    persona_words: int = 0


@dataclass
class Context:
    cfg: ExperimentConfig
    q: Questionnaire
    info: dict
    provider: Provider
    schema: dict
    out: Path

    @property
    def scale(self) -> list[int]:
        return list(self.q.scale)


def _hash(*parts: str) -> str:
    return hashlib.sha256("\x1e".join(parts).encode("utf-8")).hexdigest()


def _sum_usage(usages: list[dict]) -> dict:
    total: dict[str, int] = {}
    for u in usages:
        for k, v in u.items():
            if isinstance(v, int) and not isinstance(v, bool):
                total[k] = total.get(k, 0) + v
    return total


# Name der Studie: würde dem Modell verraten, aus welchem Datensatz die Person stammt
_STUDY_NAME = re.compile(r"European Social Survey|\bESS\d*\b")


def _id_leaks(row: dict[str, str], text: str) -> bool:
    pid = row[ID_COL]
    idno = row.get("idno", "").strip()
    return pid in text or bool(idno and re.search(rf"(?<!\d){re.escape(idno)}(?!\d)", text))


def _answers_from_log(entry: dict) -> dict[str, ItemAnswer]:
    return {k: ItemAnswer(v.get("answer_model"), v.get("probabilities"), v.get("reasoning"), v.get("probabilities_raw"))
            for k, v in entry["answers"].items()}


def _answer_log(q: Questionnaire, answers: dict[str, ItemAnswer], draws: dict[str, Draw] | None) -> dict:
    """Je Frage alle Zwischenschritte in der Reihenfolge, in der sie entstehen."""
    out = {}
    for k, item, text in zip(q.keys, q.items, q.descriptions, strict=True):
        a = answers[k]
        e = {"item": item, "question": text}
        if draws is not None:
            d = draws[k]
            e |= {"reasoning": a.reasoning, "probabilities_raw": a.probabilities_raw,
                  "probabilities": a.probabilities, "upper_bounds": d.upper_bounds,
                  "random_number": d.random_number, "answer_final": d.answer}
        else:
            e |= {"answer_model": a.answer_model, "answer_final": a.answer_model}
        out[k] = e
    return out


@dataclass
class Prepared:
    """Prompt und Metadaten einer Person, bevor das Modell gefragt wird."""
    pid: str
    persona: Persona
    system: str
    user: str
    params: dict
    prompt_hash: str


def prepare_person(row: dict[str, str], ctx: Context) -> Prepared | PersonResult:
    """Baut den Prompt. Gibt direkt ein PersonResult zurück, wenn nicht gefragt werden darf oder muss."""
    cfg, q = ctx.cfg, ctx.q
    pid = row[ID_COL]
    persona = build_persona(row, ctx.info, cfg.prompt.exclude_profile_columns)
    system = system_prompt(persona.text, cfg.prompt.anti_collapse_instruction, cfg.prompt.verbalized_sampling)
    user = user_prompt(q)
    params = ctx.provider.request_params()
    prompt_hash = _hash(system, user, json.dumps(ctx.schema, sort_keys=True), json.dumps(params, sort_keys=True))

    (ctx.out / "prompts").mkdir(parents=True, exist_ok=True)
    (ctx.out / "prompts" / f"{pid}.txt").write_text(
        f"===== SYSTEM =====\n{system}\n\n===== USER =====\n{user}\n", encoding="utf-8")

    if _id_leaks(row, system + user):
        return PersonResult(pid, False, errors=["ID oder idno steht im Prompt – Abbruch"], leak=True)
    if _STUDY_NAME.search(system + user):
        return PersonResult(pid, False, errors=["Name der Studie (ESS) steht im Prompt – Abbruch"], leak=True)

    log_path = ctx.out / "logs" / f"{pid}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if cfg.run.reuse_existing and log_path.exists():
        old = json.loads(log_path.read_text(encoding="utf-8"))
        if old.get("status") == "ok" and old.get("prompt_hash") == prompt_hash:
            answers = _answers_from_log(old)
            # die Ziehung ist deterministisch (Seed + ID) und wird mit dem aktuellen Seed neu berechnet
            draws = (sample_answers(answers, q.keys, ctx.scale, cfg.answer.sampling_seed, pid)
                     if cfg.prompt.verbalized_sampling else None)
            return PersonResult(pid, True, answers, draws, len(old["attempts"]), True,
                                usage=_sum_usage([a.get("usage", {}) for a in old["attempts"]]),
                                generic_vars=persona.generic, persona_words=persona.n_words)
    return Prepared(pid, persona, system, user, params, prompt_hash)


def evaluate_attempt(rec: dict, c: Completion | None, error: str | None,
                     ctx: Context) -> tuple[dict[str, ItemAnswer] | None, list[str]]:
    """Trägt die Antwort eines Versuchs in `rec` ein und prüft sie."""
    if c is None:
        return None, [error or "keine Antwort"]
    rec.update(stop_reason=c.stop_reason, usage=c.usage, model=c.model, request_id=c.request_id,
               thinking=c.thinking, response_text=c.text, response_raw=c.raw)
    if c.stop_reason != "end_turn":
        return None, [f"Abbruchgrund {c.stop_reason!r} statt 'end_turn'"]
    return parse_response(c.text, ctx.q.keys, ctx.scale, ctx.cfg.prompt.verbalized_sampling,
                          ctx.cfg.answer.probability_tolerance)


def finish_person(prep: Prepared, attempts: list[dict], answers: dict[str, ItemAnswer] | None,
                  errors: list[str], ctx: Context) -> PersonResult:
    """Zieht die Antworten, schreibt Log und Trace."""
    cfg, q, pid = ctx.cfg, ctx.q, prep.pid
    ok = answers is not None
    draws = (sample_answers(answers, q.keys, ctx.scale, cfg.answer.sampling_seed, pid)
             if ok and cfg.prompt.verbalized_sampling else None)
    persona = prep.persona
    entry = {
        "id": pid,
        "status": "ok" if ok else "failed",
        "prompt_hash": prep.prompt_hash,
        "request": {**prep.params, "mode": cfg.run.mode, "system": prep.system, "user": prep.user,
                    "schema": ctx.schema},
        "persona_stats": {"words": persona.n_words, "sentences": persona.n_sentences,
                          "variables": len(persona.covered), "empty_variables": persona.n_empty,
                          "generic_sentences": persona.generic},
        "attempts": attempts,
        "sampling": ({"sampling_seed": cfg.answer.sampling_seed, "rule": SAMPLING_RULE}
                     if cfg.prompt.verbalized_sampling else None),
        "answers": _answer_log(q, answers, draws) if ok else None,
    }
    (ctx.out / "logs" / f"{pid}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_trace(ctx.out / "traces" / f"{pid}.md", entry, q)
    return PersonResult(pid, ok, answers, draws, len(attempts), False, [] if ok else errors,
                        _sum_usage([a.get("usage", {}) for a in attempts]), generic_vars=persona.generic,
                        persona_words=persona.n_words)


def fill_person(row: dict[str, str], ctx: Context) -> PersonResult:
    """Direkter Modus: eine Person, Versuche nacheinander."""
    prep = prepare_person(row, ctx)
    if isinstance(prep, PersonResult):
        return prep
    attempts: list[dict] = []
    answers = None
    errors: list[str] = []
    for attempt in range(1, ctx.cfg.run.max_attempts + 1):
        rec = {"attempt": attempt, "timestamp": _dt.datetime.now().isoformat(timespec="seconds")}
        t0 = time.perf_counter()
        try:
            c, err = ctx.provider.complete(prep.system, prep.user, ctx.schema), None
        except Exception as e:  # noqa: BLE001 – jeder Fehler zählt als gescheiterter Versuch
            c, err = None, f"{type(e).__name__}: {e}"
        try:
            answers, errors = evaluate_attempt(rec, c, err, ctx)
        except Exception as e:  # noqa: BLE001
            answers, errors = None, [f"{type(e).__name__}: {e}"]
        rec["duration_s"] = round(time.perf_counter() - t0, 3)  # Dauer des API-Aufrufs inkl. SDK-Retries
        rec["errors"] = errors
        attempts.append(rec)
        if answers is not None:
            break
        log.warning("%s: Versuch %d fehlgeschlagen: %s", prep.pid, attempt, "; ".join(errors)[:300])
    return finish_person(prep, attempts, answers, errors, ctx)


def fill_batch(rows: list[dict[str, str]], ctx: Context) -> list[PersonResult]:
    """Batch-Modus: alle offenen Personen einer Runde in einem Batch; ungültige Antworten in der nächsten Runde."""
    from .batch import run_batch

    done: dict[str, PersonResult] = {}
    preps: dict[str, Prepared] = {}
    for row in rows:
        p = prepare_person(row, ctx)
        if isinstance(p, PersonResult):
            done[p.id] = p
        else:
            preps[p.pid] = p
    state = {pid: {"attempts": [], "answers": None, "errors": []} for pid in preps}
    pending = list(preps)
    for attempt in range(1, ctx.cfg.run.max_attempts + 1):
        if not pending:
            break
        ts = _dt.datetime.now().isoformat(timespec="seconds")
        res = run_batch(ctx.provider, {pid: ctx.provider.message_params(preps[pid].system, preps[pid].user,
                                                                         ctx.schema) for pid in pending},
                        ctx.out, ctx.cfg.run.batch_poll_seconds)
        still = []
        for pid in pending:
            rec = {"attempt": attempt, "timestamp": ts, "batch_id": res.batch_id,
                   "batch_duration_s": res.duration_s}
            try:
                answers, errors = evaluate_attempt(rec, res.completions.get(pid), res.errors.get(pid), ctx)
            except Exception as e:  # noqa: BLE001
                answers, errors = None, [f"{type(e).__name__}: {e}"]
            rec["errors"] = errors
            st = state[pid]
            st["attempts"].append(rec)
            st["answers"], st["errors"] = answers, errors
            if answers is None:
                still.append(pid)
                log.warning("%s: Versuch %d fehlgeschlagen: %s", pid, attempt, "; ".join(errors)[:300])
        pending = still
    for pid, st in state.items():
        done[pid] = finish_person(preps[pid], st["attempts"], st["answers"], st["errors"], ctx)
    return [done[r[ID_COL]] for r in rows]


# ---------------------------------------------------------------------------
# Lauf
# ---------------------------------------------------------------------------

def select_persons(profile: pd.DataFrame, cfg: PersonsCfg) -> pd.DataFrame:
    n = len(profile) if cfg.n is None else min(cfg.n, len(profile))
    if cfg.selection == "first":
        return profile.head(n)
    return profile.sample(n=n, random_state=cfg.seed).sort_index()


def out_dir(paths: Paths, cfg: ExperimentConfig) -> Path:
    return paths.llm_results_dir / cfg.folder


def run_fill(cfg: ExperimentConfig, paths: Paths) -> list[PersonResult]:
    out = out_dir(paths, cfg)
    out.mkdir(parents=True, exist_ok=True)
    profile = read_ess_csv(paths.profile_csv).df
    human = read_ess_csv(paths.questionnaire_csv).df
    items = [c for c in human.columns if c != ID_COL]

    info = load_variable_info(paths.missing_codes_csv, paths.codebook_html)
    texts = parse_variable_texts(paths.codebook_html)
    q = build_questionnaire(items, texts, info[items[0]].labels)
    provider = make_provider(cfg.model.provider, cfg.model.name, cfg.model.max_tokens, cfg.model.effort,
                             cfg.model.thinking)
    ctx = Context(cfg, q, info, provider, response_schema(q, cfg.prompt.verbalized_sampling), out)

    persons = select_persons(profile, cfg.persons)
    rows = persons.to_dict(orient="records")
    if cfg.run.mode == "batch":
        log.info("Befrage %d Person(en) mit %s über die Batch API", len(rows), cfg.model.name)
        results = fill_batch(rows, ctx)
    else:
        log.info("Befrage %d Person(en) mit %s (%d parallel)", len(rows), cfg.model.name,
                 cfg.run.parallel_requests)
        with ThreadPoolExecutor(max_workers=cfg.run.parallel_requests) as pool:
            results = list(pool.map(lambda r: fill_person(r, ctx), rows))

    _write_outputs(results, q, cfg, out)
    (out / "config_used.yaml").write_text(yaml.safe_dump(asdict(cfg), sort_keys=False, allow_unicode=True),
                                          encoding="utf-8")
    _write_report(results, q, cfg, paths, out, human)
    n_ok = sum(r.ok for r in results)
    log.info("Fertig: %d/%d erfolgreich -> %s", n_ok, len(results), out / QUESTIONNAIRE_CSV)
    return results


def _final(r: PersonResult) -> dict[str, int]:
    """Mit Verbalized Sampling die gezogene Antwort, sonst die des Modells."""
    if r.draws is not None:
        return {k: d.answer for k, d in r.draws.items()}
    return {k: a.answer_model for k, a in r.answers.items()}


def _write_outputs(results: list[PersonResult], q: Questionnaire, cfg: ExperimentConfig, out: Path) -> None:
    ok = [r for r in results if r.ok]

    def table(choose) -> Table:
        rows = [[r.id] + [str(choose(r)[k]) for k in q.keys] for r in ok]
        return Table(pd.DataFrame(rows, columns=[ID_COL] + q.items, dtype=str), {ID_COL})

    write_ess_csv(table(_final), out / QUESTIONNAIRE_CSV)

    # eine Zeile je Person und Frage, Spalten in der Reihenfolge der Pipeline:
    # Überlegung -> Wahrscheinlichkeiten (roh, normiert) -> Intervallgrenzen -> Zufallszahl -> finale Antwort
    detail = []
    for r in ok:
        for k, item, text in zip(q.keys, q.items, q.descriptions, strict=True):
            a = r.answers[k]
            row = {ID_COL: r.id, "frage": k, "item": item, "fragetext": text}
            if r.draws is not None:
                d = r.draws[k]
                row["begruendung"] = a.reasoning
                row |= {f"p_roh{c}": p for c, p in zip(q.scale, a.probabilities_raw or [None] * 6, strict=True)}
                row |= {f"p{c}": p for c, p in zip(q.scale, a.probabilities, strict=True)}
                row |= {f"grenze{c}": g for c, g in zip(q.scale, d.upper_bounds, strict=True)}
                row |= {"zufallszahl": d.random_number, "antwort_final": d.answer, "modus": a.mode(list(q.scale))}
            else:
                row["antwort_final"] = a.answer_model
            detail.append(row)
    pd.DataFrame(detail).to_csv(out / DETAIL_CSV, index=False)


def _write_trace(path: Path, entry: dict, q: Questionnaire) -> None:
    """Lesbare Nachverfolgung einer Person: was ging hinein, was kam zurück, wie wurde gezogen."""
    pid = entry["id"]
    req = entry["request"]
    lines = [f"# Nachverfolgung {pid}", "",
             f"- Status: **{entry['status']}** · Modell `{req.get('model')}` · Versuche: {len(entry['attempts'])}",
             f"- Prompt: [`prompts/{pid}.txt`](../prompts/{pid}.txt) · "
             f"Rohdaten: [`logs/{pid}.json`](../logs/{pid}.json)",
             f"- Profil: {entry['persona_stats']['words']} Wörter, {entry['persona_stats']['variables']} Variablen"]
    if entry.get("sampling"):
        lines.append(f"- Ziehung: Seed {entry['sampling']['sampling_seed']} – {entry['sampling']['rule']}")

    lines += ["", "## 1. Antworten des Modells je Versuch", ""]
    for a in entry["attempts"]:
        lines.append(f"### Versuch {a['attempt']} ({a['timestamp']}) – "
                     f"{'gültig' if not a['errors'] else 'ungültig: ' + '; '.join(a['errors'])[:300]}")
        if a.get("thinking"):
            lines += ["", "Denkschritte (Zusammenfassung der API):", ""]
            lines += ["> " + t.replace("\n", "\n> ") for t in a["thinking"]]
        elif "thinking" in a:
            lines += ["", "Denkschritte: keine geliefert (das Modell hat nicht oder nur intern nachgedacht)."]
        lines += ["", f"Rohantwort: {len(a.get('response_text') or '')} Zeichen, siehe Log.", ""]

    if entry["answers"]:
        lines += ["## 2. Je Frage: Überlegung → Wahrscheinlichkeiten → Ziehung", ""]
        labels = q.scale
        for k, e in entry["answers"].items():
            lines += [f"### {k} ({e['item']})", "", f"> {e['question']}", ""]
            if "random_number" not in e:
                lines += [f"Antwort des Modells: **{e['answer_final']}** ({labels[e['answer_final']]})", ""]
                continue
            lines += [f"Überlegung: {e['reasoning']}", "",
                      "| Option | Label | p (Modell) | p (normiert) | Intervall |", "|---|---|---|---|---|"]
            lower = 0.0
            for (c, lab), p_raw, p, hi in zip(labels.items(), e["probabilities_raw"] or [None] * 6,
                                              e["probabilities"], e["upper_bounds"], strict=True):
                hit = " ◀" if c == e["answer_final"] else ""
                raw = "–" if p_raw is None else f"{p_raw:g}"
                lines.append(f"| {c}{hit} | {lab} | {raw} | {p:.3f} | [{lower:.3f}, {hi:.3f}) |")
                lower = hi
            ans = e["answer_final"]
            lines += ["", f"Zufallszahl u = {e['random_number']:.4f} → liegt im Intervall von Option {ans} → "
                          f"**finale Antwort {ans}** ({labels[ans]})", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------

def _write_report(results: list[PersonResult], q: Questionnaire, cfg: ExperimentConfig, paths: Paths,
                  out: Path, human: pd.DataFrame) -> None:
    ok = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    price = cfg.model.price_per_mtok or {}

    def tokens(rs: list[PersonResult]) -> str:
        u = _sum_usage([r.usage for r in rs])
        cost = (u.get("input_tokens", 0) * price.get("input", 0)
                + u.get("output_tokens", 0) * price.get("output", 0)) / 1e6
        return f"Eingabe {u.get('input_tokens', 0):,}, Ausgabe {u.get('output_tokens', 0):,} → ca. {cost:.4f} USD"

    llm = read_ess_csv(out / QUESTIONNAIRE_CSV).df
    profile_ids = set(read_ess_csv(paths.profile_csv).df[ID_COL])
    vals = llm[q.items].apply(pd.to_numeric, errors="coerce")
    checks = [
        ("Spalten wie ESS_fragebogen_DE.csv (Reihenfolge)", list(llm.columns) == list(human.columns)),
        ("21 Antworten je Person, ganzzahlig 1–6",
         bool(vals.notna().all().all() and vals.isin(list(q.scale)).all().all())),
        ("IDs eindeutig", llm[ID_COL].is_unique),
        ("alle IDs stammen aus ESS_profil_DE.csv", set(llm[ID_COL]) <= profile_ids),
        ("ID/idno und Studienname in keinem Prompt", not any(r.leak for r in results)),
        ("alle Personen erfolgreich", not failed),
    ]

    lines = [
        f"# LLM-Lauf: {cfg.folder}",
        "",
        f"- **Modell:** `{cfg.model.provider}` / `{cfg.model.name}` (effort `{cfg.model.effort}`, "
        f"max_tokens {cfg.model.max_tokens})",
        f"- **Anti-Varianzkollaps-Anweisung:** {cfg.prompt.anti_collapse_instruction} · "
        f"**Verbalized Sampling:** {cfg.prompt.verbalized_sampling} · **finale Antwort:** "
        f"{'aus der verbalisierten Verteilung gezogen' if cfg.prompt.verbalized_sampling else 'Wahl des Modells'}",
        f"- **Personen:** {len(results)} angefragt ({cfg.persons.selection}), {len(ok)} erfolgreich, "
        f"{len(failed)} fehlgeschlagen, {sum(r.reused for r in results)} aus früherem Lauf übernommen",
        f"- **API-Aufrufe:** {sum(r.attempts for r in results if not r.reused)} "
        f"(Versuche je Person: {sorted({r.attempts for r in results})})",
        f"- **Tokens dieser Lauf:** {tokens([r for r in results if not r.reused])}",
        f"- **Tokens alle Personen (inkl. übernommene):** {tokens(results)}",
        "",
        "## Prüfungen",
        "",
        "| Prüfung | Ergebnis |",
        "|---|---|",
    ]
    lines += [f"| {name} | {'OK' if passed else '**FEHLER**'} |" for name, passed in checks]

    if failed:
        lines += ["", "## Fehlgeschlagene Personen", ""]
        lines += [f"- `{r.id}`: {'; '.join(r.errors)[:500]}" for r in failed]

    generic = sorted({v for r in ok for v in r.generic_vars})
    words = [r.persona_words for r in ok if r.persona_words]
    lines += ["", "## Profiltext", ""]
    if words:
        lines.append(f"- Länge: im Mittel {np.mean(words):.0f} Wörter (min {min(words)}, max {max(words)})")
    lines.append(f"- Variablen mit generischem Satz (keine eigene Vorlage oder Wert ohne Label): "
                 f"{', '.join(generic) if generic else 'keine'}")

    if ok:
        h = human.set_index(ID_COL).loc[llm[ID_COL], q.items].apply(pd.to_numeric)
        m = vals.set_axis(llm[ID_COL], axis=0)
        same = (h.to_numpy() == m.to_numpy()).mean()
        lines += [
            "", "## Vergleich mit den echten Antworten derselben Personen", "",
            f"- exakt gleiche Antwort: {same:.1%} der Items",
            f"- mittlere absolute Abweichung: {np.abs(h.to_numpy() - m.to_numpy()).mean():.2f} Skalenpunkte",
            f"- Standardabweichung je Item (Mittel über 21 Items): LLM {m.std(ddof=0).mean():.2f}, "
            f"Menschen {h.std(ddof=0).mean():.2f}",
        ]
        if cfg.prompt.verbalized_sampling:
            scale = list(q.scale)
            modes = np.array([[r.answers[k].mode(scale) for k in q.keys] for r in ok])
            lines.append(f"- gezogene Antwort = wahrscheinlichste Option der Verteilung: "
                         f"{(modes == m.to_numpy()).mean():.1%} der Items")
        lines += ["", "Bei sehr wenigen Personen sind diese Zahlen nur ein Funktionstest, keine Auswertung."]

    lines += ["", "## Dateien", "",
              f"- `{QUESTIONNAIRE_CSV}` – id + 21 Items (finale Antwort), Format wie ESS_fragebogen_DE.csv",
              f"- `{DETAIL_CSV}` – je Person und Frage: Überlegung, Wahrscheinlichkeiten (roh und normiert), "
              "Intervallgrenzen, Zufallszahl, finale Antwort, Modus",
              "- `traces/<id>.md` – lesbare Nachverfolgung je Person: Denkschritte, Überlegung, Verteilung, Ziehung",
              f"- `{SCORES_CSV}` – Scores (wie results/mensch/ess_scores.csv)",
              "- `prompts/<id>.txt` – System- und User-Prompt je Person",
              "- `logs/<id>.json` – Anfrage, je Versuch komplette API-Antwort (inkl. Denk-Zusammenfassung), "
              "Prüfergebnis, Token-Verbrauch, je Frage alle Zwischenschritte der Ziehung",
              "- `config_used.yaml` – verwendete Konfiguration",
              f"- Auswertung und Abbildungen (Stufe `auswertung`): `results/auswertung/{out.name}/`"]
    (out / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")
