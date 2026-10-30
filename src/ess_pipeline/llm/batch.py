"""
Phase 3 – Abfrage über die Message Batches API (50 % Rabatt, asynchron, Ergebnis meist < 1 h, höchstens 24 h).

Alle Anfragen einer Runde gehen als ein Batch an die API; die Ergebnisse kommen in beliebiger Reihenfolge
zurück und werden über `custom_id` (= Personen-ID) zugeordnet. Wiederholungsversuche für ungültige
Antworten laufen in `experiment.py` als weitere Runde (= neuer Batch).

Absicherung gegen Abbrüche (die API hält Ergebnisse 29 Tage):
- `batches.jsonl` im Ergebnisordner: ein Eintrag beim Abschicken (Batch-ID, Personen, Schlüssel der Anfragen)
  und einer nach dem Abholen – sofort geschrieben, nicht erst am Ende des Laufs.
- `batches/<batch_id>.jsonl`: die Ergebnisse der API unverändert, gespeichert vor jeder Auswertung.
- Wird der Lauf neu gestartet, setzt er einen abgeschickten, aber nicht abgeholten Batch mit identischen
  Anfragen fort, statt ihn erneut (kostenpflichtig) abzuschicken.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from .providers import AnthropicProvider, Completion

log = logging.getLogger("ess_pipeline.llm")

BATCH_LOG = "batches.jsonl"
BATCH_DIR = "batches"


@dataclass
class BatchOutcome:
    batch_id: str
    duration_s: float                                   # Abschicken (bzw. Fortsetzen) bis Ende der Verarbeitung
    completions: dict[str, Completion] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)  # Personen ohne Antwort (errored/expired/canceled)


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _key(params: dict[str, dict]) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _append(out: Path, record: dict) -> None:
    with (out / BATCH_LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _open_batch(out: Path, key: str) -> str | None:
    """ID eines abgeschickten, noch nicht abgeholten Batches mit denselben Anfragen."""
    path = out / BATCH_LOG
    if not path.exists():
        return None
    submitted, collected = {}, set()
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["event"] == "submitted":
            submitted[r["batch_id"]] = r["key"]
        elif r["event"] == "collected":
            collected.add(r["batch_id"])
    open_ids = [b for b, k in submitted.items() if k == key and b not in collected]
    return open_ids[-1] if open_ids else None


def run_batch(provider: AnthropicProvider, params: dict[str, dict], out: Path,
              poll_s: float = 30.0) -> BatchOutcome:
    """Schickt {custom_id: Aufrufparameter} als einen Batch ab und wartet auf das Ergebnis."""
    t0 = time.perf_counter()
    key = _key(params)
    batch = None
    if (resume_id := _open_batch(out, key)) is not None:
        batch = provider.client.messages.batches.retrieve(resume_id)
        if batch.processing_status == "canceling" or (batch.processing_status == "ended"
                                                     and batch.request_counts.succeeded == 0):
            batch = None
        else:
            log.info("Setze Batch %s fort (Status %s)", batch.id, batch.processing_status)
    if batch is None:
        batch = provider.client.messages.batches.create(
            requests=[{"custom_id": cid, "params": p} for cid, p in params.items()])
        _append(out, {"event": "submitted", "time": _now(), "batch_id": batch.id, "key": key,
                      "model": next(iter(params.values()))["model"], "n_requests": len(params),
                      "custom_ids": list(params)})
        log.info("Batch %s abgeschickt (%d Anfragen)", batch.id, len(params))
    while batch.processing_status != "ended":
        time.sleep(poll_s)
        batch = provider.client.messages.batches.retrieve(batch.id)
        c = batch.request_counts
        log.info("Batch %s: %s – fertig %d, in Arbeit %d, Fehler %d", batch.id, batch.processing_status,
                 c.succeeded, c.processing, c.errored + c.expired + c.canceled)

    # Rohergebnisse sichern, bevor irgendetwas ausgewertet wird
    raw_path = out / BATCH_DIR / f"{batch.id}.jsonl"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    results = list(provider.client.messages.batches.results(batch.id))
    raw_path.write_text("".join(json.dumps(r.to_dict(), ensure_ascii=False) + "\n" for r in results),
                        encoding="utf-8")

    res = BatchOutcome(batch.id, round(time.perf_counter() - t0, 3))
    for r in results:
        if r.result.type == "succeeded":
            res.completions[r.custom_id] = provider.to_completion(r.result.message)
        elif r.result.type == "errored":
            res.errors[r.custom_id] = f"Batch-Fehler: {r.result.error.error.type}: {r.result.error.error.message}"
        else:
            res.errors[r.custom_id] = f"Batch-Ergebnis {r.result.type!r}"
    for cid in set(params) - set(res.completions) - set(res.errors):
        res.errors[cid] = "Kein Ergebnis im Batch"
    c = batch.request_counts
    _append(out, {"event": "collected", "time": _now(), "batch_id": batch.id,
                  "created_at": str(batch.created_at), "ended_at": str(batch.ended_at),
                  "counts": {"succeeded": c.succeeded, "errored": c.errored, "expired": c.expired,
                             "canceled": c.canceled},
                  "raw_results": str(raw_path.relative_to(out))})
    log.info("Batch %s beendet nach %.0f s: %d Antworten, %d ohne Antwort", batch.id, res.duration_s,
             len(res.completions), len(res.errors))
    return res
