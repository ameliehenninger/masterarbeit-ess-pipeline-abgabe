# LLM-Twins von ESS-Befragten: Schwartz-Werte im Vergleich

Code zur Masterarbeit. Ein Sprachmodell bekommt das Profil einer realen Befragten des European Social Survey
(ESS Round 11, Deutschland, 2 262 Personen) und füllt in ihrer Rolle den PVQ-21 aus, den Fragebogen zu den
10 Schwartz-Werten. Dieser „Twin“ wird mit der echten Person verglichen (**Ebene 1**), die simulierte Population mit
der realen (**Ebene 2**).

- **Dokumentation** (Methoden, Entscheidungen, Begründungen): [`DOKUMENTATION.md`](DOKUMENTATION.md)
- **Ergebnis des Hauptexperiments:**
  [`results/auswertung/claude-haiku-5-5_low_batch_all/report.md`](results/auswertung/claude-haiku-5-5_low_batch_all/report.md)
- **Abbildungen:** [`results/auswertung/claude-haiku-5-5_low_batch_all/figures/`](results/auswertung/claude-haiku-5-5_low_batch_all/figures/)
  (je Abbildung PNG und Beschreibung) und [`results/mensch/figures/`](results/mensch/figures/)

## Schnellstart

Voraussetzungen: [uv](https://docs.astral.sh/uv/) und die ESS-Rohdaten. Berichte und Abbildungen unter `results/` lassen
sich ohne diese Schritte direkt ansehen.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # 1. uv installieren (einmal pro Rechner)
uv sync --extra dev                                    # 2. Python 3.10 und alle Pakete laut uv.lock installieren
                                                       # 3. Rohdaten nach data/raw/ legen, siehe data/raw/README.md
uv run python run_pipeline.py                          # 4. Phase 1 + 2: Bereinigung, Scores, Prüfungen (ca. 1 min)
uv run python run_llm.py --stages score analyse auswertung   # 5. Phase 3 (ohne API) + Phase 4 (ca. 2 min)
uv run pytest                                          # 6. Tests
```

Schritt 4 und 5 brauchen keinen API-Schlüssel: Schritt 5 rechnet mit den gespeicherten Antworten des Modells. Die neu
erzeugten Dateien landen unter `results/` und überschreiben die mitgelieferten.

## Ablauf

| Phase | Was | Start | Doku |
|---|---|---|---|
| 1 Bereinigung | ESS-Rohdaten → vollständige deutsche Befragungsdaten, getrennt in Profil und Fragebogen | `python run_pipeline.py --stages clean` | [Abschnitt 2](DOKUMENTATION.md#2-phase-1-daten-und-bereinigung) |
| 2 Scores | 10 Basiswerte, 4 Higher-Order Values, x/y im Wertekreis; 18 Prüfungen | `python run_pipeline.py --stages score validate plot` | [Abschnitt 3](DOKUMENTATION.md#3-phase-2-schwartz-werte-berechnen) |
| 3 LLM-Experiment | LLM füllt den PVQ-21 je Person aus (narratives Profil, Verbalized Sampling, Batch-API); Scores der Twins; Verteilungsanalyse | `python run_llm.py --stages fill score analyse` | [Abschnitt 4](DOKUMENTATION.md#4-phase-3-das-llm-füllt-den-fragebogen-aus) |
| 4 Auswertung | Ebene 1 (Twin ↔ Person) und Ebene 2 (Population ↔ Population) entlang der Forschungsfragen | `python run_llm.py --stages auswertung` | [Abschnitt 5](DOKUMENTATION.md#5-phase-4-auswertung) |

## Umgebung einrichten

Das Projekt hat eine eigene Python-Umgebung, verwaltet mit [uv](https://docs.astral.sh/uv/): `.python-version` legt
Python 3.10 fest, `uv.lock` die exakten Versionen aller Pakete. `uv sync --extra dev` legt die Umgebung in `.venv` an.

Danach Befehle mit `uv run …` starten oder die Umgebung aktivieren (`source .venv/bin/activate`). Die Befehle unten
setzen die aktivierte Umgebung voraus. `requirements.txt` ist aus dem Lockfile erzeugt und nur für Installationen ohne
uv gedacht.

## Reproduzieren

Die Befehle aus dem [Schnellstart](#schnellstart) erzeugen die mitgelieferten Ergebnisse aus den Rohdaten neu. Die
Auswertung verwendet Seed 42. Auf einem anderen Rechner oder Betriebssystem können numerische Werte in den hinteren
Nachkommastellen abweichen. In einem Kontrolllauf lag die größte relative Abweichung bei 7 · 10⁻⁸ (Bures-Wasserstein)
und veränderte keine in der Arbeit berichtete gerundete Zahl.

Das LLM erneut befragen (`fill`) braucht einen Anthropic-API-Schlüssel (`export ANTHROPIC_API_KEY=…`). Alle
Einstellungen stehen in [`config/llm_experiment.yaml`](config/llm_experiment.yaml). Personen mit erfolgreichem Log
und identischem Prompt werden aus `logs/` übernommen und nicht noch einmal abgefragt. Im Repository liegen `logs/` und
`prompts/` nur als Beispiel vor (siehe [`results/llm/README.md`](results/llm/README.md)), `fill` fragt also alle Personen neu ab.

```bash
python run_llm.py                                                              # alle Stufen, Hauptexperiment
python run_llm.py --config config/vorexperiment_which_thinking_mode/opus.yaml  # ein Lauf des Vorexperiments
python run_llm.py --n 10                                                       # Personenzahl überschreiben
```

Weitere Optionen: `python run_pipeline.py --help`, `python run_llm.py --help`.

## Projektstruktur

```
├── run_pipeline.py              Einstieg Phase 1 + 2
├── run_llm.py                   Einstieg Phase 3 + 4
├── config/
│   ├── llm_experiment.yaml      Hauptexperiment: Haiku 5.5, effort low, ohne Thinking, Batch, alle Personen
│   └── vorexperiment_which_thinking_mode/   6 Läufe mit 100 Personen zur Wahl von Modell, effort und Thinking
├── src/ess_pipeline/
│   ├── config.py                Pfade, PVQ-Item-Zuordnung, Parameter
│   ├── csv_io.py, codebook.py   ESS-CSV lesen/schreiben, Missing-Codes aus dem Codebook
│   ├── cleaning.py              Phase 1: Schritte 1–8
│   ├── scoring.py               Phase 2: Scores (auch für die Twins)
│   ├── validation.py, plotting.py   Phase 2: Prüfungen, Abbildungen
│   ├── pipeline.py              Kommandozeile Phase 1 + 2
│   ├── llm/                     Phase 3: Profiltext, Prompt, API, Antwortprüfung, Ziehung, Verteilungsanalyse
│   └── analysis/                Phase 4: Paarung, Ebene 1, Ebene 2, Forschungsfragen-Auswertung, Abbildungen
├── tests/                       pytest: Unit-Tests, Regressionstest, Verifikation der Scores
├── data/
│   ├── raw/                     Anleitung zum Download der ESS-11-Rohdaten (Daten selbst nicht enthalten)
│   └── processed/               Bereinigungsbericht; bereinigte Daten erzeugt run_pipeline.py lokal
├── results/
│   ├── mensch/                  Phase 2: Scores, Prüfbericht und Abbildungen der ESS-Personen
│   ├── llm/                     Phase 3: Daten der LLM-Twins (Antworten, Traces, Scores, Verteilungsanalyse)
│   │   ├── claude-haiku-5-5_low_batch_all/      Hauptexperiment
│   │   └── vorexperiment_which_thinking_mode/   6 Läufe des Vorexperiments
│   └── auswertung/              Phase 4: Vergleich Mensch vs. LLM-Twin, je Lauf ein Ordner
│       └── claude-haiku-5-5_low_batch_all/      Report, Kennzahlen, figures/ (eine Abbildung je Unterfrage)
└── DOKUMENTATION.md             die gesamte Methodendokumentation
```

Alle `.md`-Dateien unter `data/` und `results/` erzeugt der Code automatisch (Berichte, Traces); sie werden nicht von
Hand bearbeitet. Was in einem Ergebnisordner liegt, erklärt
[Abschnitt 4.6](DOKUMENTATION.md#46-modellaufruf-und-protokoll) der Dokumentation.

## Tests

```bash
uv run pytest                # alle Tests (ca. 1 min)
uv run pytest -m "not slow"  # ohne die langsamen Tests, die die Rohdaten brauchen
uv run ruff check .          # Linting
```

Tests, die ESS-Daten brauchen, werden ohne `data/raw/` übersprungen. Der Regressionstest (`tests/test_regression.py`) prüft per SHA-256, dass die Pipeline aus den Rohdaten immer
exakt dieselben Dateien erzeugt.

## Daten und Lizenz

Die ESS-Rohdaten (`data/raw/`) und die daraus bereinigten Datensätze (`data/processed/*.csv`) sind nicht im Repository.
Sie sind nach einer Anmeldung kostenlos im [ESS-Datenportal](https://ess.sikt.no/en/datafile/242aaa39-3bbb-40f5-98bf-bfb1ce53d8ef) erhältlich. Download und Einordnung beschreibt
[`data/raw/README.md`](data/raw/README.md).

Das ESS stellt seine Daten unter [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) bereit und
[empfiehlt](https://www.europeansocialsurvey.org/contact/disclaimer), Datensätze nicht auf externen Seiten anzubieten,
sondern auf das Datenportal zu verweisen. Die Dateien unter `results/` enthalten aus diesen Daten abgeleitete Angaben
(unter anderem Scores je Person). Sie stehen unter denselben Bedingungen, siehe [`results/LICENSE.md`](results/LICENSE.md).
Die Profiltexte je Person sind bis auf ein Beispiel nicht enthalten, siehe [`results/llm/README.md`](results/llm/README.md). Diese Arbeit ist nicht mit dem
ESS ERIC verbunden oder von ihm autorisiert.
