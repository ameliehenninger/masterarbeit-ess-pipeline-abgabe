"""
Phase 3 – Austauschbare Sprachmodelle.

Jeder Anbieter implementiert `complete(system, user, schema) -> Completion`. Welcher
Anbieter und welches Modell verwendet werden, steht in config/llm_experiment.yaml
(`model.provider`, `model.name`). Neue Anbieter (z. B. ein Base Model ohne Chat-Tuning
für Experiment 1) werden in `make_provider` registriert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Completion:
    text: str
    stop_reason: str | None
    usage: dict = field(default_factory=dict)
    model: str = ""
    request_id: str | None = None
    thinking: list[str] = field(default_factory=list)  # Zusammenfassung(en) der Denkschritte, falls geliefert
    raw: dict = field(default_factory=dict)            # komplette Antwort der API, unverändert


class Provider(Protocol):
    name: str

    def complete(self, system: str, user: str, schema: dict) -> Completion: ...

    def request_params(self) -> dict:
        """Parameter des Aufrufs (ohne Prompts) – für das Log."""
        ...


class AnthropicProvider:
    """
    Claude über die Messages API; die Antwort wird per JSON-Schema (Structured Outputs) erzwungen.
    thinking "adaptive" mit display "summarized": Die API liefert eine lesbare Zusammenfassung der Denkschritte
    (das rohe Denken gibt sie nie heraus; ohne diese Einstellung bleibt der Text bei Claude Haiku 5.5 leer).
    thinking "disabled" schaltet das Denken ab (Claude Haiku 5.5: nur bis effort high; Claude Opus 5.5: nie erlaubt).
    """

    THINKING_MODES = {"adaptive": {"type": "adaptive", "display": "summarized"}, "disabled": {"type": "disabled"}}

    def __init__(self, model: str, max_tokens: int, effort: str | None, thinking: str = "adaptive",
                 max_retries: int = 5) -> None:
        import anthropic

        if thinking not in self.THINKING_MODES:
            raise ValueError(f"model.thinking muss adaptive oder disabled sein, nicht {thinking!r}")
        self.name = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.thinking = self.THINKING_MODES[thinking]
        # Schlüssel aus ANTHROPIC_API_KEY bzw. `ant auth login`
        self.client = anthropic.Anthropic(max_retries=max_retries)

    def request_params(self) -> dict:
        return {"provider": "anthropic", "model": self.name, "max_tokens": self.max_tokens,
                "thinking": self.thinking, "effort": self.effort}

    def message_params(self, system: str, user: str, schema: dict) -> dict:
        """Parameter eines Aufrufs – gleich für den direkten Aufruf und die Batch API."""
        output_config: dict = {"format": {"type": "json_schema", "schema": schema}}
        if self.effort:
            output_config["effort"] = self.effort
        return {"model": self.name, "max_tokens": self.max_tokens, "system": system,
                "messages": [{"role": "user", "content": user}], "thinking": self.thinking,
                "output_config": output_config}

    @staticmethod
    def to_completion(resp, request_id: str | None = None) -> Completion:
        text = "".join(b.text for b in resp.content if b.type == "text")
        thinking = [b.thinking for b in resp.content if b.type == "thinking" and b.thinking]
        return Completion(text, resp.stop_reason, resp.usage.to_dict(), resp.model, request_id,
                          thinking, resp.to_dict())

    def complete(self, system: str, user: str, schema: dict) -> Completion:
        resp = self.client.messages.create(**self.message_params(system, user, schema))
        return self.to_completion(resp, resp._request_id)


def make_provider(provider: str, model: str, max_tokens: int, effort: str | None,
                  thinking: str = "adaptive") -> Provider:
    if provider == "anthropic":
        return AnthropicProvider(model, max_tokens, effort, thinking)
    raise ValueError(f"Unbekannter Anbieter {provider!r} – in llm/providers.py:make_provider ergänzen")
