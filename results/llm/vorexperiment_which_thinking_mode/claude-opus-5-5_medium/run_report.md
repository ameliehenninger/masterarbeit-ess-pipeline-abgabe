# LLM-Lauf: claude-opus-5-5_medium

- **Modell:** `anthropic` / `claude-opus-5-5` (effort `medium`, max_tokens 16000)
- **Anti-Varianzkollaps-Anweisung:** True · **Verbalized Sampling:** True · **finale Antwort:** aus der verbalisierten Verteilung gezogen
- **Personen:** 10 angefragt (first), 10 erfolgreich, 0 fehlgeschlagen, 0 aus früherem Lauf übernommen
- **API-Aufrufe:** 10 (Versuche je Person: [1])
- **Tokens dieser Lauf:** Eingabe 66,344, Ausgabe 19,483 → ca. 0.6550 USD
- **Tokens alle Personen (inkl. übernommene):** Eingabe 66,344, Ausgabe 19,483 → ca. 0.6550 USD

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Spalten wie ESS_fragebogen_DE.csv (Reihenfolge) | OK |
| 21 Antworten je Person, ganzzahlig 1–6 | OK |
| IDs eindeutig | OK |
| alle IDs stammen aus ESS_profil_DE.csv | OK |
| ID/idno und Studienname in keinem Prompt | OK |
| alle Personen erfolgreich | OK |

## Profiltext

- Länge: im Mittel 2577 Wörter (min 2453, max 2618)
- Variablen mit generischem Satz (keine eigene Vorlage oder Wert ohne Label): keine

## Vergleich mit den echten Antworten derselben Personen

- exakt gleiche Antwort: 28.6% der Items
- mittlere absolute Abweichung: 1.15 Skalenpunkte
- Standardabweichung je Item (Mittel über 21 Items): LLM 1.10, Menschen 1.04
- gezogene Antwort = wahrscheinlichste Option der Verteilung: 32.9% der Items

Bei sehr wenigen Personen sind diese Zahlen nur ein Funktionstest, keine Auswertung.

## Dateien

- `fragebogen_LLM.csv` – id + 21 Items (finale Antwort), Format wie ESS_fragebogen_DE.csv
- `antworten_LLM_detail.csv` – je Person und Frage: Überlegung, Wahrscheinlichkeiten (roh und normiert), Intervallgrenzen, Zufallszahl, finale Antwort, Modus
- `traces/<id>.md` – lesbare Nachverfolgung je Person: Denkschritte, Überlegung, Verteilung, Ziehung
- `scores_LLM.csv` – Scores (wie results/mensch/ess_scores.csv)
- `prompts/<id>.txt` – System- und User-Prompt je Person
- `logs/<id>.json` – Anfrage, je Versuch komplette API-Antwort (inkl. Denk-Zusammenfassung), Prüfergebnis, Token-Verbrauch, je Frage alle Zwischenschritte der Ziehung
- `config_used.yaml` – verwendete Konfiguration
- `figures/` – Abbildungen wie für die Menschen
