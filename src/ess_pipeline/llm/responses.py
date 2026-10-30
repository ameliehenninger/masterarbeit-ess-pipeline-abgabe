"""
Phase 3 – Antwort des LLM prüfen und finale Antworten bestimmen.

Prüfungen je Antwort (jede Verletzung = Fehler, der Versuch wird wiederholt):
  - gültiges JSON {"answers": [...]}, jede Frage Q1–Q21 genau einmal
  - mit Verbalized Sampling: je Frage sechs Wahrscheinlichkeiten, endlich und >= 0, Summe 1 ± Toleranz
  - ohne Verbalized Sampling: Antwort ganzzahlig auf der Skala (1–6)

Finale Antwort mit Verbalized Sampling: wie im Paper (Zhang et al. 2026, Dialogsimulation) wählt nicht
das Modell, sondern dieses Programm zieht je Frage eine Antwort aus der verbalisierten, auf Summe 1
normierten Verteilung – reproduzierbar über Seed + Personen-ID. Ohne Verbalized Sampling ist die
finale Antwort die des Modells.

Die Ziehung ist offengelegt, damit jeder Schritt im Log nachvollziehbar ist: Je Frage wird eine
Zufallszahl u aus [0, 1) gezogen. Die Wahrscheinlichkeiten teilen [0, 1) in sechs aufeinanderfolgende
Intervalle (kumulierte Summen); gewählt wird die Option, in deren Intervall u fällt. Beispiel:
p = (0.1, 0.2, 0.4, 0.2, 0.1, 0) -> Intervalle bis 0.1, 0.3, 0.7, 0.9, 1.0, 1.0; u = 0.53 -> Option 3.
"""

from __future__ import annotations

import json
import math
import zlib
from dataclasses import dataclass

import numpy as np


@dataclass
class ItemAnswer:
    answer_model: int | None = None               # nur ohne Verbalized Sampling
    probabilities: list[float] | None = None      # auf Summe 1 normiert, Reihenfolge wie Skala
    reasoning: str | None = None
    probabilities_raw: list[float] | None = None  # genau so, wie das Modell sie angegeben hat

    def mode(self, scale: list[int]) -> int:
        """Wahrscheinlichste Option (bei Gleichstand die erste)."""
        return scale[int(np.argmax(self.probabilities))]


def parse_response(text: str, keys: list[str], scale: list[int], verbalized_sampling: bool,
                   tolerance: float) -> tuple[dict[str, ItemAnswer] | None, list[str]]:
    """(Antworten je Schlüssel, Fehlerliste). Bei Fehlern ist das erste Element None."""
    try:
        raw = json.loads(text)
    except (json.JSONDecodeError, TypeError) as e:
        return None, [f"kein gültiges JSON: {e}"]
    if not isinstance(raw, dict) or not isinstance(raw.get("answers"), list):
        return None, ['JSON hat nicht die Form {"answers": [...]}']

    errors: list[str] = []
    asked = [e.get("question") if isinstance(e, dict) else None for e in raw["answers"]]
    dupes = sorted({k for k in asked if asked.count(k) > 1}, key=str)
    if dupes:
        errors.append(f"doppelt beantwortet: {dupes}")
    data = {e["question"]: e for e in raw["answers"] if isinstance(e, dict) and e.get("question") in keys}
    missing = [k for k in keys if k not in data]
    extra = [k for k in asked if k not in keys]
    if missing:
        errors.append(f"fehlende Fragen: {missing}")
    if extra:
        errors.append(f"unbekannte Fragen: {extra}")

    out: dict[str, ItemAnswer] = {}
    for k in keys:
        entry = data.get(k)
        if not isinstance(entry, dict):
            if k not in missing:
                errors.append(f"{k}: kein Objekt")
            continue
        if not verbalized_sampling:
            ans = entry.get("answer")
            if isinstance(ans, bool) or not isinstance(ans, int) or ans not in scale:
                errors.append(f"{k}: Antwort {ans!r} nicht in {scale}")
                continue
            out[k] = ItemAnswer(answer_model=ans)
            continue
        raw = entry.get("probabilities")
        if not isinstance(raw, dict) or sorted(raw) != sorted(str(c) for c in scale):
            errors.append(f"{k}: Wahrscheinlichkeiten fehlen oder falsche Schlüssel")
            continue
        vals = [raw[str(c)] for c in scale]
        if not all(isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v) and v >= 0
                   for v in vals):
            errors.append(f"{k}: ungültige Wahrscheinlichkeit in {vals}")
            continue
        total = float(sum(vals))
        if abs(total - 1) > tolerance:
            errors.append(f"{k}: Summe der Wahrscheinlichkeiten {total:.3f} (erlaubt 1 ± {tolerance})")
            continue
        reasoning = entry.get("reasoning")
        out[k] = ItemAnswer(probabilities=[v / total for v in vals],
                            reasoning=reasoning if isinstance(reasoning, str) else None,
                            probabilities_raw=[float(v) for v in vals])
    return (None, errors) if errors else (out, [])


@dataclass
class Draw:
    answer: int               # gezogene Option = finale Antwort
    random_number: float      # u aus [0, 1)
    upper_bounds: list[float]  # obere Intervallgrenze je Option (kumulierte Wahrscheinlichkeiten)


def rng_for(seed: int, person_id: str) -> np.random.Generator:
    """Eigener Zufallsgenerator je Person: gleiche Seed + ID -> gleiche Ziehung, unabhängig von der Reihenfolge."""
    return np.random.default_rng([seed, zlib.crc32(person_id.encode("utf-8"))])


def draw_one(probabilities: list[float], scale: list[int], u: float) -> Draw:
    # auf 12 Stellen gerundet, damit Grenzen exakt sind (0.1 + 0.2 + 0.4 = 0.7, nicht 0.7000000000000001)
    upper = np.round(np.cumsum(probabilities), 12)
    upper[-1] = 1.0  # das letzte Intervall endet genau bei 1
    i = min(int(np.searchsorted(upper, u, side="right")), len(scale) - 1)
    return Draw(scale[i], u, [float(x) for x in upper])


def sample_answers(answers: dict[str, ItemAnswer], keys: list[str], scale: list[int],
                   seed: int, person_id: str) -> dict[str, Draw]:
    """Je Frage (in Fragebogenreihenfolge) eine Zufallszahl ziehen und die zugehörige Option bestimmen."""
    rng = rng_for(seed, person_id)
    return {k: draw_one(answers[k].probabilities, scale, float(rng.random())) for k in keys}
