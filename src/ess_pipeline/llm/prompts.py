"""
Phase 3 – Prompt-Bausteine: System-Prompt, leerer PVQ-21-Fragebogen, Antwortschema.

    System-Prompt = Situation (Interview) + narratives Profil ("Who you are")
                    + Anleitung (Anti-Varianzkollaps-Anweisung, Verbalized Sampling oder direkte Antwort)
    User-Prompt   = PVQ-21 im englischen Wortlaut des ESS-Codebooks, Items neutral als Q1–Q21 nummeriert

Das Modell bekommt nur, was eine befragte Person auch hätte: die Interviewsituation, wer sie ist und den
Fragebogen. Weder Forschungskontext noch ESS-Variablennamen (ipcrtiva, …) noch der Name der Studie kommen
im Prompt vor, damit das Modell nicht auf auswendig gelernte ESS-Ergebnisse zurückgreift
(vgl. Dalloul & Pfeifer 2026). Die Anleitung steht nach dem langen Profil, direkt vor dem Fragebogen.

Verbalized Sampling (Zhang et al. 2026, Variante VS-CoT): Das Modell überlegt kurz und gibt dann für jede
der sechs Antwortoptionen eine Wahrscheinlichkeit an. Es wählt selbst keine Antwort – die finale Antwort
wird außerhalb des Modells aus dieser Verteilung gezogen (responses.sample_answers).
"""

from __future__ import annotations

from dataclasses import dataclass

SITUATION = (
    "You are taking part in a face-to-face interview for a social survey. The interviewer is about to hand you "
    "a questionnaire. Who you are is described below, under \"Who you are\". Answer every question as this "
    "person, from your own life, experiences and views. There are no right, wrong or socially desirable answers."
)

# Experiment 2 (DOKUMENTATION.md, Abschnitt 4.1), ohne Fachbegriffe ("mode collapse") und ohne Zwang zu
# Extremwerten (Begründung in Abschnitt 4.4)
ANTI_COLLAPSE = (
    "Answer exactly and without compromise as the person described. Do not give the answers an average person "
    "or a typical respondent would give, and do not soften your views towards the middle of the scale: where "
    "your views are strong, specific or unusual, your answers should show it."
)

# Technik 2: Verbalized Sampling (Zhang et al. 2026), Variante VS-CoT – erst überlegen, dann die Verteilung
VERBALIZED_SAMPLING = (
    "For each question:\n"
    "1. reasoning: In one or two sentences, in your own voice, think about what in your life and views makes "
    "the description more or less like you.\n"
    "2. probabilities: Give, for each of the six answer options, the probability (from 0.0 to 1.0) that you "
    "would choose it. The six probabilities must add up to 1. Put most of the weight on one option if you are "
    "sure, and spread it over several options if you are not.\n"
    "Answer every question (Q1–Q21) exactly once, in order, in the required JSON format."
)

DIRECT = ("For each question, choose the one answer option that fits you best. Answer every question (Q1–Q21) "
          "exactly once, in order, in the required JSON format.")


@dataclass(frozen=True)
class Questionnaire:
    items: list[str]          # ESS-Variablennamen in Fragebogenreihenfolge
    intro: str                # Einleitung (für alle Items gleich)
    descriptions: list[str]   # Beschreibung je Item (ohne Einleitung)
    scale: dict[int, str]     # 1 -> "Very much like me", …

    @property
    def keys(self) -> list[str]:
        """Neutrale Schlüssel im Prompt und in der Antwort: Q1, Q2, …"""
        return [f"Q{i}" for i in range(1, len(self.items) + 1)]


def build_questionnaire(items: list[str], texts: dict[str, list[str]], labels: dict[str, str]) -> Questionnaire:
    """
    items  = PVQ-Spalten in der Reihenfolge von ESS_fragebogen_DE.csv
    texts  = codebook.parse_variable_texts(...)  (Titel, Fragetext)
    labels = Code -> Label des ersten Items (Antwortskala, ohne Missing-Codes)
    """
    marker = "Use this card for your answer. "
    questions = [texts[i][1] for i in items]
    intros = {q.split(marker, 1)[0] + marker.strip() for q in questions}
    if len(intros) != 1 or not all(marker in q for q in questions):
        raise ValueError("PVQ-Items haben im Codebook nicht die erwartete gemeinsame Einleitung")
    descriptions = [q.split(marker, 1)[1].strip() for q in questions]
    scale = {int(c): lab for c, lab in labels.items()}
    if sorted(scale) != [1, 2, 3, 4, 5, 6]:
        raise ValueError(f"Unerwartete Antwortskala: {scale}")
    return Questionnaire(list(items), intros.pop(), descriptions, dict(sorted(scale.items())))


def system_prompt(persona_text: str, anti_collapse: bool, verbalized_sampling: bool) -> str:
    instructions = [ANTI_COLLAPSE] if anti_collapse else []
    instructions.append(VERBALIZED_SAMPLING if verbalized_sampling else DIRECT)
    return "\n\n".join([SITUATION, "# Who you are\n\n" + persona_text,
                        "# How to answer\n\n" + "\n\n".join(instructions)])


def user_prompt(q: Questionnaire) -> str:
    lines = [q.intro, "", "Answer options:"]
    lines += [f"{code} = {label}" for code, label in q.scale.items()]
    lines.append("")
    lines += [f"{key}. {desc}" for key, desc in zip(q.keys, q.descriptions, strict=True)]
    return "\n".join(lines)


def _object(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def response_schema(q: Questionnaire, verbalized_sampling: bool) -> dict:
    """
    JSON-Schema für output_config.format.
        mit Verbalized Sampling: {"answers": [{question, reasoning, probabilities}, …]} – keine eigene Antwort
        ohne:                    {"answers": [{question, answer}, …]}

    Eine Liste statt 21 fester Schlüssel, weil die API sonst die Grammatik als zu groß ablehnt
    ("compiled grammar is too large"). Dass genau Q1–Q21 je einmal vorkommen, prüft responses.parse_response.
    Die Reihenfolge der Felder ist die Reihenfolge, in der das Modell sie schreibt.
    """
    codes = [str(c) for c in q.scale]
    item = {"question": {"type": "string", "enum": q.keys}}
    if verbalized_sampling:
        item |= {"reasoning": {"type": "string"},
                 "probabilities": _object({c: {"type": "number"} for c in codes})}
    else:
        item["answer"] = {"type": "integer", "enum": [int(c) for c in codes]}
    return _object({"answers": {"type": "array", "items": _object(item)}})
