# Hinweis zu `prompts/` und `logs/`

Die Ordner `prompts/` und `logs/` enthalten je Person das fast vollständige ESS-Profil als Fließtext. Das ESS empfiehlt,
Datensätze nicht auf externen Seiten anzubieten. Deshalb liegt hier nur das Beispiel `DE_50032` aus dem Hauptlauf.

Die Verweise auf andere Personen in `traces/` führen darum ins Leere. Antworten, Ziehungen und Scores aller Personen
sind vollständig enthalten (`fragebogen_LLM.csv`, `antworten_LLM_detail.csv`, `scores_LLM.csv`, `traces/`, `batches/`).
Die Prompts lassen sich aus den ESS-Daten mit `run_llm.py` neu erzeugen, die vollständigen Dateien liegen der
Verfasserin vor und können für die Prüfung bereitgestellt werden.
