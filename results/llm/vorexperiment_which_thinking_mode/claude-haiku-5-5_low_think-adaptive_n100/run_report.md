# LLM-Lauf: claude-haiku-5-5_low_think-adaptive_n100

- **Modell:** `anthropic` / `claude-haiku-5-5` (effort `low`, max_tokens 16000)
- **Anti-Varianzkollaps-Anweisung:** True · **Verbalized Sampling:** True · **finale Antwort:** aus der verbalisierten Verteilung gezogen
- **Personen:** 100 angefragt (first), 100 erfolgreich, 0 fehlgeschlagen, 0 aus früherem Lauf übernommen
- **API-Aufrufe:** 100 (Versuche je Person: [1])
- **Tokens dieser Lauf:** Eingabe 655,367, Ausgabe 197,220 → ca. 0.1641 USD
- **Tokens alle Personen (inkl. übernommene):** Eingabe 655,367, Ausgabe 197,220 → ca. 0.1641 USD

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

- Länge: im Mittel 2550 Wörter (min 2078, max 2687)
- Variablen mit generischem Satz (keine eigene Vorlage oder Wert ohne Label): keine

## Vergleich mit den echten Antworten derselben Personen

- exakt gleiche Antwort: 26.4% der Items
- mittlere absolute Abweichung: 1.31 Skalenpunkte
- Standardabweichung je Item (Mittel über 21 Items): LLM 1.33, Menschen 1.12
- gezogene Antwort = wahrscheinlichste Option der Verteilung: 39.0% der Items

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
