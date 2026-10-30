# LLM-Lauf: claude-haiku-5-5_low_batch_all

- **Modell:** `anthropic` / `claude-haiku-5-5` (effort `low`, max_tokens 16000)
- **Anti-Varianzkollaps-Anweisung:** True · **Verbalized Sampling:** True · **finale Antwort:** aus der verbalisierten Verteilung gezogen
- **Personen:** 2262 angefragt (first), 2262 erfolgreich, 0 fehlgeschlagen, 0 aus früherem Lauf übernommen
- **API-Aufrufe:** 2262 (Versuche je Person: [1])
- **Tokens dieser Lauf:** Eingabe 14,893,457, Ausgabe 4,496,273 → ca. 1.8687 USD
- **Tokens alle Personen (inkl. übernommene):** Eingabe 14,893,457, Ausgabe 4,496,273 → ca. 1.8687 USD

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

- Länge: im Mittel 2560 Wörter (min 1729, max 2721)
- Variablen mit generischem Satz (keine eigene Vorlage oder Wert ohne Label): keine

## Vergleich mit den echten Antworten derselben Personen

- exakt gleiche Antwort: 25.5% der Items
- mittlere absolute Abweichung: 1.34 Skalenpunkte
- Standardabweichung je Item (Mittel über 21 Items): LLM 1.35, Menschen 1.17
- gezogene Antwort = wahrscheinlichste Option der Verteilung: 38.5% der Items

Bei sehr wenigen Personen sind diese Zahlen nur ein Funktionstest, keine Auswertung.

## Dateien

- `fragebogen_LLM.csv` – id + 21 Items (finale Antwort), Format wie ESS_fragebogen_DE.csv
- `antworten_LLM_detail.csv` – je Person und Frage: Überlegung, Wahrscheinlichkeiten (roh und normiert), Intervallgrenzen, Zufallszahl, finale Antwort, Modus
- `traces/<id>.md` – lesbare Nachverfolgung je Person: Denkschritte, Überlegung, Verteilung, Ziehung
- `scores_LLM.csv` – Scores (wie results/mensch/ess_scores.csv)
- `prompts/<id>.txt` – System- und User-Prompt je Person
- `logs/<id>.json` – Anfrage, je Versuch komplette API-Antwort (inkl. Denk-Zusammenfassung), Prüfergebnis, Token-Verbrauch, je Frage alle Zwischenschritte der Ziehung
- `config_used.yaml` – verwendete Konfiguration
- Auswertung und Abbildungen (Stufe `auswertung`): `results/auswertung/claude-haiku-5-5_low_batch_all/`
