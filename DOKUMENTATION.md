# Dokumentation

Methoden, Entscheidungen und Begründungen der ganzen Pipeline. Einrichtung, Befehle und Projektstruktur stehen in der
[README](README.md).

## Inhalt

- [1. Fragestellung und Aufbau](#1-fragestellung-und-aufbau)
  - [1.1 Forschungsfragen](#11-forschungsfragen)
  - [1.2 Ablauf](#12-ablauf)
- [2. Phase 1: Daten und Bereinigung](#2-phase-1-daten-und-bereinigung)
  - [2.1 Rohdaten](#21-rohdaten)
  - [2.2 Die acht Schritte](#22-die-acht-schritte)
  - [2.3 Schritt 8: keine Hinweise auf den Datensatz im Profil](#23-schritt-8-keine-hinweise-auf-den-datensatz-im-profil)
- [3. Phase 2: Schwartz-Werte berechnen](#3-phase-2-schwartz-werte-berechnen)
  - [3.1 Anforderungen](#31-anforderungen)
  - [3.2 Berechnung](#32-berechnung)
  - [3.3 Ausgabe](#33-ausgabe)
  - [3.4 Prüfung](#34-prüfung)
  - [3.5 Beispielrechnung: Person DE_50032](#35-beispielrechnung-person-de_50032)
- [4. Phase 3: Das LLM füllt den Fragebogen aus](#4-phase-3-das-llm-füllt-den-fragebogen-aus)
  - [4.1 Ausgangsproblem Varianzkollaps und Versuchsplan](#41-ausgangsproblem-varianzkollaps-und-versuchsplan)
  - [4.2 Ablauf der Stufe fill](#42-ablauf-der-stufe-fill)
  - [4.3 Technik 1: das narrative Profil („Who you are“)](#43-technik-1-das-narrative-profil-who-you-are)
  - [4.4 Aufbau des Prompts](#44-aufbau-des-prompts)
  - [4.5 Technik 2: Verbalized Sampling](#45-technik-2-verbalized-sampling)
  - [4.6 Modellaufruf und Protokoll](#46-modellaufruf-und-protokoll)
  - [4.7 Vorexperiment: Welches Modell und welcher Thinking-Modus?](#47-vorexperiment-welches-modell-und-welcher-thinking-modus)
    - [4.7.1 Methodik und Versuchsplan](#471-methodik-und-versuchsplan)
    - [4.7.2 Tokens, Kosten und Dauer](#472-tokens-kosten-und-dauer)
    - [4.7.3 Qualität und Varianzkollaps](#473-qualität-und-varianzkollaps)
    - [4.7.4 Analyse der Wahrscheinlichkeitsvektoren](#474-analyse-der-wahrscheinlichkeitsvektoren)
  - [4.8 Hauptlauf](#48-hauptlauf)
- [5. Phase 4: Auswertung](#5-phase-4-auswertung)
  - [5.1 Herleitung der Metriken](#51-herleitung-der-metriken)
  - [5.2 Daten vorbereiten](#52-daten-vorbereiten)
  - [5.3 Vergleichsgrößen: Woher kommt die Nähe?](#53-vergleichsgrößen-woher-kommt-die-nähe)
  - [5.4 Ebene 1: Twin ↔ Person](#54-ebene-1-twin--person)
  - [5.5 Ebene 2: Population ↔ Population](#55-ebene-2-population--population)
  - [5.6 Sensitivitätsanalyse: Ebene 1 mit gezogenen Antworten](#56-sensitivitätsanalyse-ebene-1-mit-gezogenen-antworten)
  - [5.7 Ausgabe](#57-ausgabe)
- [6. Grenzen und offene Punkte](#6-grenzen-und-offene-punkte)
- [7. Literatur](#7-literatur)

---

## 1. Fragestellung und Aufbau

Wie gut kann ein Sprachmodell eine reale Person simulieren? Ein LLM bekommt das Profil einer echten Befragten des
European Social Survey (ESS Round 11, Deutschland) und füllt in ihrer Rolle den PVQ-21 aus, den Fragebogen zu den
10 Schwartz-Werten. Es sieht dabei nicht die echten Antworten, die Reihenfolge der Fragen ist identisch. Der PVQ-21
beschreibt 21 kurze Personenporträts („Es ist ihm wichtig, neue Dinge auszuprobieren“); die befragte Person gibt auf
einer Skala von 1 („Very much like me“) bis 6 („Not like me at all“) an, wie ähnlich sie ihr ist.

### 1.1 Forschungsfragen

**Hauptforschungsfrage:** In welchem Ausmaß reproduzieren LLM-generierte
synthetische Befragte die multivariate Wertestruktur und die daraus abgeleitete personenzentrierte Segmentstruktur
einer realen ESS-PVQ21-Stichprobe?

Die Hauptforschungsfrage lässt sich nur beantworten, wenn beide Forschungsfragen beantwortet sind. Sie werden auf
zwei Ebenen untersucht: FF1 (Ebene 1) misst die Vorhersagegenauigkeit für die einzelne Person (Mikroebene), FF2
(Ebene 2) die Struktur der ganzen simulierten Population (Makroebene). Jede Forschungsfrage ist in Unterfragen
zerlegt:

- **Hauptforschungsfrage**
  - **FF1 · Ebene 1: Twin ↔ Person** – Kennt das LLM die Person oder nur die Bevölkerung?
    - **1a Genauigkeit:** Wie weit liegt der Twin daneben, und ist er besser als ohne Personenwissen?
    - **1b Profil:** Trifft er die Rangfolge der Werte, und was davon ist persönlich?
    - **1b′ Trennschärfe:** Unterscheidet er die Personen je Item besser als die Demografie?
    - **1c Bias:** Sind die Fehler gerichtet, und bei welchen Werten?
    - **1d Subgruppen:** Bei welchen Gruppen gelingt es schlechter?
    - **1e Varianzkollaps:** Streuen Twins gleicher Demografie zu wenig?
  - **FF2 · Ebene 2: Population ↔ Population** – Ist die synthetische Stichprobe als Ersatz brauchbar?
    - **2.0 Vorfrage:** Gibt es überhaupt getrennte Milieus?
    - **2a Lage:** Liegen die Milieus an derselben Stelle?
    - **2b Streuung:** Sind sie gleich breit?
    - **2c Form:** Sind sie gleich geformt?
    - **2d Zuordnung:** Landen die Twins im Milieu ihrer Person?
    - **Fazit 3 Werte oder Demografie:** Spiegeln die Twins Werte oder nur Demografie?

Dazu kommen drei Abbildungen ohne eigene Unterfrage, die das Lesen der übrigen erleichtern: **A1** (eine
Beispielperson: wie aus sechs Wahrscheinlichkeiten eine Antwort wird), **A2** (Varianzzerlegung: wie viel der
Twin-Streuung Information ist und wie viel Ziehung) und **A3** (je Person: Ist ihr Twin besser als ihre Vergleichsgrößen?).

| Ebene | Forschungsfrage |
|---|---|
| **Ebene 1** – Twin ↔ Person | **FF1:** Wie genau kann ein LLM, das nur das ESS-Profil einer realen Person kennt, deren individuelle Antworten auf den PVQ-21 reproduzieren, und bei welchen Gruppen gelingt das schlechter? Enthält der simulierte Twin dabei Information über die einzelne Person, die über allgemeines Wissen zur Bevölkerung hinausgeht? |
| **Ebene 2** – Population ↔ Population | **FF2:** Bildet die simulierte Population dieselbe Wertestruktur wie die reale? Liegen die Werte-Milieus an derselben Stelle, sind sie gleich breit und gleich geformt, landen die Twins im Milieu ihrer Vorbilder, und spiegeln sie Werte oder nur Demografie? |

Welche Metrik welche Unterfrage beantwortet und warum, steht in Abschnitt 5. Der Bericht endet mit einer
zusammenfassenden Antwort auf die Hauptforschungsfrage.

**Einordnung: Proof of Concept für den Evaluationsrahmen.** Der Beitrag der Arbeit ist der Rahmen, mit dem sich
LLM-Twins auf beiden Ebenen prüfen lassen: Vergleichsgrößen ohne Personenwissen, die Trennung von Antwortstil und
inhaltlicher Umgewichtung, die Varianzzerlegung und die Milieu-Vergleiche. Angewendet wird er auf genau ein Modell
(Claude Haiku 5.5), ein Prompt-Design (narratives Profil mit Verbalized Sampling) und einen Lauf. Die Ergebnisse
zeigen, was der Rahmen sichtbar macht; sie sind keine allgemeine Aussage über LLM-Twins (Grenzen in Abschnitt 6).

### 1.2 Ablauf

```
                          data/raw/ESS.csv
                                 │
                                 ▼
                        Phase 1 Bereinigung
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
     Profil (wer ist die Person)     Fragebogen (21 echte Antworten)
                 │                     = Menschen-Datensatz
                 ▼                               │
   Phase 3 LLM spielt die Person                 │
                 │                               │
                 ▼                               │
        21 Twin-Antworten                        │
                 │                               │
                 ▼                               ▼
      Phase 2 Scores (Twin)           Phase 2 Scores (Mensch)      gleiche Formel für beide
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
          Phase 4 Auswertung: Mensch ↔ Twin, gepaart über die ID
            (Antworten und Scores beider Seiten, Ebene 1 + 2)
```

Das Prinzip: **Mensch und Twin durchlaufen genau dieselbe Verarbeitung.** Ein Unterschied liegt dann am LLM und
nicht an der Verarbeitung.

---

## 2. Phase 1: Daten und Bereinigung

Code: [`cleaning.py`](src/ess_pipeline/cleaning.py). Start: `python run_pipeline.py --stages clean`.
Ziel: den ESS-Originaldatensatz auf vollständige deutsche Befragungsdaten reduzieren, getrennt in Profil und
Fragebogen.

### 2.1 Rohdaten

| Ordner | Inhalt | Erzeugt durch |
|---|---|---|
| `data/raw/` | `ESS.csv` (ESS Round 11, Integrated file, Edition 4.2, 50 116 Personen × 691 Spalten), `ESS11_Dokumentation.html` (Codebook) | Download von ess.sikt.no |
| `data/interim/` | Zwischenstand jedes Schritts (`schritt_2/` … `schritt_8/`), nicht versioniert | `run_pipeline.py --save-intermediate` |
| `data/processed/` | `ESS_fragebogen_DE.csv`, `ESS_profil_DE.csv` (je 2 262 Personen), `ESS_missing_codes.csv`, `cleaning_report.md` | `run_pipeline.py` |

Die Daten in `data/raw/` und die CSV-Dateien in `data/processed/` liegen aus Lizenzgründen nicht im Repository
(siehe README, Abschnitt „Daten und Lizenz“).

Rohdaten beschaffen: auf <https://ess.sikt.no> anmelden, ESS Round 11 (Integrated file, Edition 4.2) als CSV
herunterladen und als `data/raw/ESS.csv` speichern, die Variablendokumentation (HTML) als
`data/raw/ESS11_Dokumentation.html`. Prüfen, ob es genau die verwendete Version ist:

```bash
shasum -a 256 data/raw/ESS.csv                   # 4b0bfa73fa86bcf9f868b0a6145f96504a40d7e3f2deeb3e822555993ab32dc8
shasum -a 256 data/raw/ESS11_Dokumentation.html  # 316801aea7f1ae802a92f77c620adc672af24b3bb378711c29aedda5ecbe9ab6
```

### 2.2 Die acht Schritte

| # | Schritt | Genaue Regel | Anmerkung | Wirkung |
|---|---|---|---|---|
| 1 | Einlesen | `data/raw/ESS.csv` unverändert, alle Werte als Text | Codes wie `07` oder `77` bleiben unverändert | Rohdaten: 50 116 Personen × 691 Spalten |
| 2 | Split | ID `id = <cntry>_<idno>` (z. B. `DE_50032`). Fragebogen = `id` + 21 PVQ-Items, Profil = `id` + übrige 670 Spalten | Das LLM sieht nur das Profil; der Fragebogen ist die „Lösung“ | Profil: 671 Spalten, Fragebogen: 22 Spalten |
| 3 | Nur Deutschland | `cntry ≠ DE` entfernen | eine Population, ein Kulturkontext | 2 420 Personen |
| 4 | Leere Spalten | Spalten löschen, die für alle Personen leer sind | in DE nicht gestellte Fragen wären Ballast im Prompt | 251 Spalten gelöscht → Profil: 420 Spalten |
| 5 | Überwiegend 0 | Spalten löschen, in denen **mehr als 50 %** exakt den Wert `0` haben | Reduktion der Profilspalten | 127 Spalten gelöscht → Profil: 293 Spalten |
| 6 | Missing-Codes | alle im Codebook mit `*` als „Missing value“ markierten Codes (z. B. 66, 77, 88, 99; je Variable verschieden, etwa 6666, 7777) → leer. Die Codes liest die Pipeline aus dem Codebook und speichert sie als `ESS_missing_codes.csv` | „weiß nicht“ darf weder als Zahl gerechnet noch als Antwort beschrieben werden | 133 376 Zellen geleert |
| 7 | Unvollständige Personen | Personen mit mindestens einer leeren Zelle **in den 21 Items** entfernen; leere Profil-Zellen bleiben erlaubt | Scores und Vergleich brauchen alle 21 Antworten. Im Rohdatensatz ist keine Item-Zelle leer, fehlende Antworten sind dort Codes; deshalb greift dieser Schritt erst nach Schritt 6 | 158 Personen entfernt → **2 262 Personen** |
| 8 | Metadaten, Doppelkodierungen | Profilspalten aus `config.PROFILE_DROP_GROUPS` löschen (2.3) | keine Information über die Person, könnte aber auf den ESS verweisen | 35 Spalten gelöscht → **Profil: 258 Spalten** |

Profil und Fragebogen werden immer über die ID abgeglichen, nie über die Zeilenposition. Zeilen und Spalten nach
jedem Schritt sowie die Listen aller gelöschten Spalten stehen im automatisch erzeugten
[`data/processed/cleaning_report.md`](data/processed/cleaning_report.md).

`tests/test_regression.py` prüft per SHA-256, dass die Pipeline aus den Rohdaten immer exakt dieselben Dateien
erzeugt.

### 2.3 Schritt 8: keine Hinweise auf den Datensatz im Profil

Das Profil geht in Phase 3 als Text an ein Sprachmodell. Falls der ESS in dessen Trainingsdaten war, sollen Spalten
ohne Information über die Person keine Wiedererkennung auslösen. Gelöscht werden:
- Survey-Metadaten: `name`, `essround`, `edition`, `proddate`, `regunit`, `mode`, `recon`
- Interview-Zeitstempel: `inwds`, `ainws` … `jinwe`, `inwtm` (16 Spalten)
- Geschlecht doppelt: `nobingnd` (in DE für alle identisch mit `gndr`), `icgndra` (Einschätzung der
  Interviewerin bzw. des Interviewers)
- Alter doppelt: `yrbrn`, `agegroup` (`agea` bleibt)
- Bildung doppelt: ISCED (`edulvl*b`) und ES-ISCED (`eisced*`) für Person, Partner/in, Vater, Mutter. Beide sind
  aus den deutschen Abschlüssen abgeleitet, die bleiben (`edu*de1`, `edu*de2`). Geprüft: Wo ISCED gefüllt ist,
  ist immer auch ein deutscher Abschluss gefüllt.

Gewichte (`dweight`, `pspwght`, `pweight`, `anweight`) und Stichprobendesign (`domain`, `prob`, `stratum`, `psu`)
bleiben für gewichtete Auswertungen in den Daten, kommen aber nicht in den Prompt
(`prompt.exclude_profile_columns`). Nachkodierte Variablen wie `maritalb` und `mnactic` bleiben ebenfalls: Sie
sind für über 1 000 Personen die einzige Angabe.

---

## 3. Phase 2: Schwartz-Werte berechnen

Code: [`scoring.py`](src/ess_pipeline/scoring.py) (Berechnung), [`validation.py`](src/ess_pipeline/validation.py)
(18 Prüfungen), [`plotting.py`](src/ess_pipeline/plotting.py) (Abbildungen). Start:
`python run_pipeline.py --stages score validate plot`.

Aus den 21 PVQ-Items werden die **10 Schwartz-Basiswerte**, die **4 Higher-Order Values** und die Position im
Wertekreis berechnet.

### 3.1 Anforderungen

- **Wiederverwendbar:** Dieselbe Funktion rechnet später die Scores der Twins. Sie baut nichts ESS-Spezifisches fest
  ein; Item-Zuordnung, ID-Spalte und Hedonism-Zuordnung kommen als Parameter herein.
- **Eingaben unverändert:** Profil- und Fragebogen-CSV werden nur gelesen (geprüft per SHA-256, 3.4).
- **IDs:** Die ID-Spalte wird als Text gelesen (`dtype=str`), damit keine führenden Nullen verloren gehen und nichts
  in Gleitkommazahlen umgewandelt wird. Daten werden nie über die Zeilenposition zugeordnet, immer über die ID.
- **Eingabezustand:** Nach Phase 1 hat jede Person alle 21 Items mit einem Wert von 1 bis 6 beantwortet. Fehlt eine
  Item-Spalte oder liegt ein Wert außerhalb, bricht die Funktion mit den betroffenen IDs ab, statt weiterzurechnen.

**Antwortskala** (für alle 21 Items gleich, keine invertierten Items):

| Code | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Label | Very much like me | Like me | Somewhat like me | A little like me | Not like me | Not like me at all |

### 3.2 Berechnung

```
21 Rohitems (1–6)
   │  Stufe 1: umpolen  x' = 7 − x
   ▼
21 umgepolte Items ──► Stufe 2: MRAT = Mittel aller 21
   │
   ├─► Stufe 3: 10 Basiswerte  = Item-Mittel − MRAT
   ├─► Stufe 4: 4 Higher-Order = Mittel der zentrierten Basiswerte   (kein weiteres MRAT)
   ▼
Stufe 5: x/y-Koordinaten aus den 4 Higher-Order Values
```

| Stufe | Was | Warum |
|---|---|---|
| 1 | umpolen `x' = 7 − x` für alle 21 Items | danach 6 = „sehr wichtig“; sonst hätte jeder Score das falsche Vorzeichen |
| 2 | MRAT = Mittel aller 21 umgepolten Items | Antwortstil einer Person (manche kreuzen alles hoch an) |
| 3 | 10 Basiswerte = Itemmittel − MRAT | Schwartz: es zählt die *relative* Wichtigkeit |
| 4 | 4 Higher-Order Values = ungewichtetes Mittel der zentrierten Basiswerte | jeder Basiswert zählt gleich; erneut MRAT abziehen wäre doppelt zentriert |
| 5 | `x = SELFTRANS − SELFENH`, `y = OPEN − CONS` | Position im Wertekreis; MRAT kürzt sich heraus |

| Basiswert | Items | Higher-Order Value | Basiswerte (Items) | Formel |
|---|---|---|---|---|
| SD Self-Direction (Selbstbestimmung: eigenständig denken, wählen und handeln) | `ipcrtiva`, `impfreea` | **OPEN** Openness to Change | SD, ST, HE (6 Items) | (SD + ST + HE) / 3 |
| ST Stimulation | `impdiffa`, `ipadvnta` | | | |
| HE Hedonism | `ipgdtima`, `impfuna` | | | |
| AC Achievement | `ipshabta`, `ipsucesa` | **SELFENH** Self-Enhancement | AC, PO (4 Items) | (AC + PO) / 2 |
| PO Power | `impricha`, `iprspota` | | | |
| SE Security | `impsafea`, `ipstrgva` | **CONS** Conservation | SE, CO, TR (6 Items) | (SE + CO + TR) / 3 |
| CO Conformity | `ipfrulea`, `ipbhprpa` | | | |
| TR Tradition | `ipmodsta`, `imptrada` | | | |
| BE Benevolence | `iphlppla`, `iplylfra` | **SELFTRANS** Self-Transcendence | UN, BE (5 Items) | (UN + BE) / 2 |
| UN Universalism | `ipeqopta`, `ipudrsta`, `impenva` (/ 3) | | | |

Jedes Item gehört zu genau einem Basiswert. Die Higher-Order Values sind das **ungewichtete Mittel der bereits
MRAT-zentrierten Basiswerte**, also z. B. OPEN = (SD + ST + HE) / 3; es wird kein weiteres MRAT abgezogen. Jeder
Basiswert zählt damit gleich, unabhängig von seiner Item-Zahl. Bei OPEN, CONS und SELFENH (zwei Items je Basiswert) ist
das identisch mit dem Mittel der gepoolten Items minus MRAT (z. B. OPEN = Summe der 6 Items / 6 − MRAT). Nur bei
SELFTRANS unterscheiden sich die Wege, weil UN drei Items hat und BE zwei: (UN + BE) / 2 gewichtet beide Basiswerte
gleich, das gepoolte Mittel der 5 Items wäre (3·UN + 2·BE) / 5. Der typische Fehler wäre, nach dem Mitteln noch einmal
MRAT abzuziehen; die Abweichung wäre dann genau MRAT.

**Hedonism-Zuordnung:** Hedonism zählt zu OPEN (`hedonism_to = "openness"`, Schwartz' Scoring Key für die
ESS-Skala). Damit gilt OPEN = (SD + ST + HE) / 3 mit 6 Items und SELFENH = (AC + PO) / 2 mit 4 Items. Als
Parameter möglich sind außerdem `"both"` (HE zählt zu OPEN und SELFENH, SELFENH = (AC + PO + HE) / 3) und `"none"`
(HE zählt zu keiner Dimension, OPEN = (SD + ST) / 2). Basiswert-Listen und Divisoren passen sich jeweils an.

**Koordinaten im Wertekreis:**

| Spalte | Achse | Formel | Deutung |
|---|---|---|---|
| `x` | Selbsttranszendenz ↔ Selbststärkung | `SELFTRANS − SELFENH` | > 0: Fokus auf andere und Gemeinwohl; < 0: Fokus auf eigenen Erfolg und Status |
| `y` | Offenheit ↔ Bewahrung | `OPEN − CONS` | > 0: Wandel und Unabhängigkeit; < 0: Sicherheit und Tradition |

Bei diesen Differenzen wird nicht erneut zentriert; MRAT kürzt sich ohnehin heraus.

### 3.3 Ausgabe

`results/mensch/ess_scores.csv` mit den Spalten

```
id, MRAT, SD, ST, HE, AC, PO, SE, CO, TR, BE, UN, OPEN, CONS, SELFENH, SELFTRANS, x, y
```

Die Basiswerte stehen in Kreisreihenfolge, damit benachbarte Werte auch in der Tabelle nebeneinander liegen. Die ID
steht vorn mit demselben Spaltennamen wie in den Eingaben, die Zeilen in der Reihenfolge des Fragebogens, die Werte
ungerundet. Daneben erzeugt die Pipeline `ess_scores_README.md` mit Eingabedatei, Datum, `hedonism_to`,
Spaltenbeschreibung und allen Formeln. Abbildungen: `results/mensch/figures/`.

### 3.4 Prüfung

**18 automatische Prüfungen** ([`validation.py`](src/ess_pipeline/validation.py), Bericht in
[`results/mensch/validation_report.txt`](results/mensch/validation_report.txt), alle bestanden). Jede meldet
BESTANDEN oder FEHLGESCHLAGEN; die Gruppe D meldet statt eines Fehlschlags nur eine WARNUNG.

| # | Prüfung | Regel |
|---|---|---|
| | **A. Struktur und IDs** | |
| 1 | Gleiche Zeilenzahl | Profil, Fragebogen und Scores haben gleich viele Zeilen |
| 2 | Eindeutige IDs | keine doppelte ID in einer der drei Dateien |
| 3 | Identische ID-Mengen | alle drei Dateien haben dieselben IDs; Abweichungen werden aufgelistet |
| 4 | Gleiche Reihenfolge | ID-Spalte der Scores elementweise gleich der des Fragebogens |
| 5 | Eingaben unverändert | SHA-256 von Profil und Fragebogen vor und nach dem Lauf gleich |
| 6 | Vollständigkeit | keine NaN, genau 18 Spalten (ID + 17) |
| | **B. Eingaben** | |
| 7 | Items vorhanden | alle 21 Item-Spalten existieren, sonst Fehler |
| 8 | Wertebereich | alle Items ganzzahlig in {1, …, 6}, keine leeren Zellen, sonst Fehler mit IDs |
| | **C. Rechnung** | |
| 9 | Zweitberechnung | 50 zufällige IDs (fester Seed) mit einer separaten, einfachen Schleifen-Implementierung neu rechnen, die die Person per ID nachschlägt; Toleranz 10⁻⁹. Fängt Rechenfehler und vertauschte IDs ab |
| 10 | Merge-Test | Fragebogen und Scores per ID zusammenführen, alle Scores neu rechnen und vergleichen |
| 11 | Summen-Identität | `2·SD + 2·ST + 2·HE + 2·AC + 2·PO + 2·SE + 2·CO + 2·TR + 2·BE + 3·UN = 0` je Person (folgt aus der Zentrierung) |
| 12 | Higher-Order-Formeln | Higher-Order Values gleich dem Mittel ihrer Basiswerte, z. B. SELFTRANS = (UN + BE) / 2; `x = SELFTRANS − SELFENH`, `y = OPEN − CONS` |
| 13 | MRAT | MRAT = 7 − Zeilenmittel der Rohitems |
| 14 | Synthetische Fälle | 21 × dieselbe Antwort ergibt alle Scores, x und y = 0; eine handgerechnete Person ergibt die erwarteten Werte; `"both"` und `"none"` liefern die erwarteten Item-Mengen und Werte |
| | **D. Plausibilität (Warnung)** | |
| 15 | Wertebereiche | MRAT in [1, 6], zentrierte Scores, x und y in [−5, 5]; Werte außerhalb [−3, 3] werden gezählt |
| 16 | Wertehierarchie | im Mittel BE und UN unter den höchsten, PO unter den niedrigsten Werten; sonst ist vermutlich das Umpolen falsch |
| 17 | Gegensätze | r(OPEN, CONS) und r(SELFENH, SELFTRANS) negativ, Werte werden ausgegeben |
| 18 | Zusammenfassung | n, Mittel, SD (Standardabweichung; ab hier steht SD in statistischen Angaben immer dafür, nicht für den Basiswert Self-Direction), Min, Max je Score-Spalte |

**Unabhängige Nachrechnung** (`tests/test_verification.py`, nutzt bewusst keinen Pipeline-Code):

1. **Exakte Brüche.** Ein separates Skript liest `ESS_fragebogen_DE.csv` mit Pythons `csv` und rechnet jede Person
   in einer Schleife mit `fractions.Fraction`. Maximale Abweichung zu `ess_scores.csv`: 8,9·10⁻¹⁶ (Gleitkomma).
2. **Zentrierung.** Bei korrekter MRAT-Zentrierung gilt je Person exakt
   `2·SD + 2·ST + 2·HE + 2·AC + 2·PO + 2·SE + 2·CO + 2·TR + 2·BE + 3·UN = 0`. Mit Brüchen: exakt 0 für alle 2 262.
3. **Higher-Order auf zwei Wegen.** Für OPEN, CONS und SELFENH stimmt das Mittel der Basiswerte für alle Personen
   exakt mit dem gepoolten Item-Mittel − MRAT überein, SELFTRANS ist exakt (UN + BE) / 2; doppelte Zentrierung ist
   damit ausgeschlossen (die Abweichung wäre sonst genau MRAT).
4. **Plausibilität.** Wertehierarchie BE > UN > … > PO wie in der Literatur; r(OPEN, CONS) = −0,71,
   r(SELFENH, SELFTRANS) = −0,48, also die erwartete bipolare Struktur.

### 3.5 Beispielrechnung: Person `DE_50032`

**Umpolen** (roh → umgepolt): SD ipcrtiva 2→5, impfreea 1→6 · ST impdiffa 2→5, ipadvnta 3→4 · HE ipgdtima 2→5,
impfuna 3→4 · AC ipshabta 3→4, ipsucesa 5→2 · PO impricha 5→2, iprspota 2→5 · SE impsafea 3→4, ipstrgva 4→3 ·
CO ipfrulea 4→3, ipbhprpa 5→2 · TR ipmodsta 3→4, imptrada 5→2 · BE iphlppla 1→6, iplylfra 2→5 · UN ipeqopta 2→5,
ipudrsta 2→5, impenva 2→5

**MRAT:** Summe 86 → 86/21 = **4,0952**

| | Rechnung | exakt | Wert |
|---|---|---|---|
| SD | (5+6)/2 − 86/21 | 59/42 | +1,4048 |
| ST | (5+4)/2 − 86/21 | 17/42 | +0,4048 |
| HE | (5+4)/2 − 86/21 | 17/42 | +0,4048 |
| AC | (4+2)/2 − 86/21 | −23/21 | −1,0952 |
| PO | (2+5)/2 − 86/21 | −25/42 | −0,5952 |
| SE | (4+3)/2 − 86/21 | −25/42 | −0,5952 |
| CO | (3+2)/2 − 86/21 | −67/42 | −1,5952 |
| TR | (4+2)/2 − 86/21 | −23/21 | −1,0952 |
| BE | (6+5)/2 − 86/21 | 59/42 | +1,4048 |
| UN | (5+5+5)/3 − 86/21 | 19/21 | +0,9048 |
| OPEN | 29/6 − 86/21 | 31/42 | +0,7381 |
| CONS | 18/6 − 86/21 | −23/21 | −1,0952 |
| SELFENH | 13/4 − 86/21 | −71/84 | −0,8452 |
| SELFTRANS | (UN + BE)/2 = (11/2 + 5)/2 − 86/21 | 97/84 | +1,1548 |
| x | SELFTRANS − SELFENH | 2 | **+2,0** |
| y | OPEN − CONS | 11/6 | **+1,8333** |

Probe Zentrierung: 2·(−1,3571) + 3·0,9048 = 0 ✓. Kontrolle OPEN = (SD + ST + HE)/3 = 0,7381 ✓. Deutung: Quadrant
„offen & selbsttranszendent“; am wichtigsten Self-Direction und Benevolence, am unwichtigsten Conformity. Alle Werte
stimmen mit `ess_scores.csv` überein.

---

## 4. Phase 3: Das LLM füllt den Fragebogen aus

Code: [`src/ess_pipeline/llm/`](src/ess_pipeline/llm/). Start: `python run_llm.py` (Stufen `fill` → `score` →
`analyse` → `auswertung`). Alle Einstellungen: [`config/llm_experiment.yaml`](config/llm_experiment.yaml).

| Datei | Aufgabe |
|---|---|
| `cli.py` | Kommandozeile, Stufen |
| `experiment.py` | Ablauf des Laufs und je Person, Logs, Bericht |
| `persona.py` | Profilzeile → narrativer Fließtext („Who you are“) |
| `prompts.py` | System-Prompt, User-Prompt (Fragebogen), JSON-Schema |
| `providers.py` | Aufruf des Sprachmodells (Anthropic Messages API) |
| `batch.py` | Message Batches API |
| `responses.py` | Antwort prüfen, finale Antwort aus der Verteilung ziehen |
| `distributions.py` | Analyse der Wahrscheinlichkeitsvektoren |

### 4.1 Ausgangsproblem Varianzkollaps und Versuchsplan

Lässt man ein Sprachmodell als Befragte antworten, trifft es den Mittelwert der Bevölkerung oft gut. Die Antworten
verschiedener Personas liegen aber dicht beieinander, als würde immer dieselbe „repräsentative“ Person antworten.

- [Dalloul & Pfeifer 2026] zeigen das für Inflationserwartungen mit fünf LLMs (S. 2–3, Abb. 1; Abschnitt 3.1). Selbst
  bei 1 911 verschiedenen Personas entsprechen die Begründungen nur „a handful of different people“ (S. 8). Ursachen
  (Fazit, S. 26): **auswendig gelernte Umfrageergebnisse** („data leakage“) und ein **struktureller Sog der
  Wahrscheinlichkeitsmasse zum Mittelwert**.
- [Zhang et al. 2026] führen den Kollaps auf das Alignment zurück (Abschnitt 3): Menschliche Bewerter*innen
  bevorzugen typische Texte („typicality bias“), RLHF spitzt die Verteilung deshalb auf ihren Modus zu.

**Versuchsplan.** Gegen den Kollaps sieht das Design drei Techniken aus der Literatur vor:

| Technik | Idee | Quelle | Umsetzung |
|---|---|---|---|
| 1 Narratives Profil | Merkmale als zusammenhängende Hintergrundgeschichte statt Stichpunktliste; narrativer Kontext soll es dem Modell erleichtern, eine vom Durchschnitt abweichende Person zu verkörpern | Moon et al. (2024): *Virtual Personas for Language Models via an Anthology of Backstories* | umgesetzt (4.3) |
| 2 Verbalized Sampling | Das Modell gibt für jede der sechs Antwortoptionen eine Wahrscheinlichkeit an und begründet sie kurz; das durchbricht den direkten Pfad zur Durchschnittsantwort | [Zhang et al. 2026] | umgesetzt (4.5) |
| 3 Base Model | Modell ohne RLHF, weil das Alignment („Sicherheitstraining“) der Hauptauslöser für den Hang zu Konsens und Durchschnitt ist (Typicality Bias) | Pfeifer (2026), *Can LLMs Replace Survey Respondents? How unlearning fixes mode collapse in synthetic survey replies*, und Literatur zur Alignment-Tax | nicht umgesetzt (Abschnitt 6) |

Daraus folgen zwei Experimente, beide mit Technik 1 und 2:

- **Experiment 1: Base Model.** Ein Open-Source-Grundmodell ohne Chat-Tuning (z. B. Llama-3-Base), das ohne
  „Bravheits-Training“ auf sein rohes Trainingswissen zurückgreift.
- **Experiment 2: instruiertes Top-Modell.** Ein aktuelles High-End-Modell mit einem stark direktiven System-Prompt,
  der das Modell ausdrücklich auf das Problem hinweist. Die ursprünglich vorgesehene Anweisung lautete: *„Schlüpfe
  exakt und kompromisslos in die Rolle des beschriebenen Profils. Vermeide unter allen Umständen den
  ‚Varianzkollaps' oder ‚Mode Collapse'. Antworte nicht wie ein durchschnittlicher KI-Assistent oder der
  Bevölkerungsdurchschnitt, sondern repräsentiere ausschließlich die extremen, spezifischen und eckigen Ansichten
  genau dieser einen Person.“*

Umgesetzt ist **Experiment 2** mit Claude Haiku 5.5 (Modellwahl in 4.7). Wo die Umsetzung vom ursprünglichen
Plan abweicht, steht das mit Begründung bei der jeweiligen Technik: Wortlaut der Anweisung (4.4) und Ziehung der
finalen Antwort durch das Programm statt durch das Modell (4.5).

### 4.2 Ablauf der Stufe `fill`

1. **Config laden und prüfen.** Unbekannte Einträge sind ein Fehler; `id` muss in `prompt.exclude_profile_columns`
   stehen. `--n` überschreibt `persons.n`.
2. **Ausgabeordner** `results/llm/<run_name>/` (leer → Modellname; Unterordner erlaubt).
3. **Daten laden:** Profil (daraus entsteht der Text) und echte Antworten (Reihenfolge der Items, später Vergleich).
4. **Codebook:** je Variable Titel und Fragetext aus dem HTML-Codebook, Antwort-Labels ohne Missing-Codes aus
   `ESS_missing_codes.csv` (z. B. `domicil` 4 → „Country village“).
5. **Leeren Fragebogen bauen:** englischer Codebook-Wortlaut der 21 Items, getrennt an „Use this card for your
   answer.“ in gemeinsame Einleitung (wird geprüft) und Porträt; Skala muss genau 1–6 sein. Die ESS-Variablennamen
   werden durch neutrale Schlüssel `Q1`–`Q21` ersetzt.
6. **API-Client und JSON-Schema** (Structured Outputs) vorbereiten.
7. **Personen auswählen:** `first` = erste *n* Zeilen, `random` mit `persons.seed`; `n` leer = alle 2 262.
8. **Jede Person befragen**, bis zu `run.parallel_requests` gleichzeitig, jede in einem eigenen leeren Chat:

| | Schritt | Code |
|---|---|---|
| 8a | Profilzeile → narrativer Fließtext (4.3) | `persona.build_persona` |
| 8b | System-Prompt: Situation + Profil + Anleitung (4.4) | `prompts.system_prompt` |
| 8c | User-Prompt: leerer Fragebogen | `prompts.user_prompt` |
| 8d | Hash über Prompts, Schema und Modellparameter | `_hash` |
| 8e | Prompt speichern: `prompts/<id>.txt` | |
| 8f | **Leak-Prüfung:** Stehen ID, `idno` oder der Studienname („European Social Survey“, „ESS…“) im Prompt? → Abbruch für diese Person | `_id_leaks` |
| 8g | **Wiederverwendung:** erfolgreiches Log mit identischem Hash → Antwort übernehmen (`run.reuse_existing`) | |
| 8h | **Modellaufruf.** Gültig nur bei `stop_reason == "end_turn"` und fehlerfreiem `parse_response`, sonst neuer Versuch bis `run.max_attempts` | `provider.complete` |
| 8i | **Finale Antwort ziehen** aus der Verteilung (4.5) | `responses.sample_answers` |
| 8j | Alles protokollieren in `logs/<id>.json`, lesbar in `traces/<id>.md` | `_write_trace` |

`parse_response` prüft: Form `{"answers": [...]}`; jede Frage Q1–Q21 genau einmal, keine unbekannten; je Frage sechs
endliche Wahrscheinlichkeiten ≥ 0 mit Summe 1 ± 0,02 (`answer.probability_tolerance`), danach auf 1 normiert (Rohwerte
bleiben im Log). Das Schema ist eine Liste von Objekten statt 21 fester Schlüssel, weil die API eine zu große
Grammatik ablehnt.

Die Stufe `score` rechnet aus `fragebogen_LLM.csv` mit **demselben Code** wie in Phase 2 die Scores der Twins; `analyse` wertet die Wahrscheinlichkeitsvektoren aus (4.7.4).

### 4.3 Technik 1: das narrative Profil („Who you are“)

Die Merkmale werden nicht als Stichpunktliste übergeben, sondern als zusammenhängender englischer Text in der
zweiten Person. Narrativer Kontext soll es dem Modell erleichtern, eine vom Durchschnitt abweichende Person zu
verkörpern.

**Einschränkung aus der Literatur.** Bei [Dalloul & Pfeifer 2026] verhinderten realistische Personas allein den
Kollaps nicht (S. 8; Tab. 3, S. 10); zusätzliche Details machten die *Texte* vielfältiger, nicht die *Zahlenantworten*
(Fußnote 1, S. 16). Das Profil ist hier deshalb notwendige Grundlage, aber kein ausreichendes Mittel. Anders als deren
Vorlage mit sieben demografischen Feldern (Abb. 5, S. 17) werden hier **alle** nicht leeren Profilvariablen
verwendet, im Mittel rund 200 je Person, auch Einstellungen, Vertrauen, Gesundheit, Religion und Geschlechterrollen.

So erzeugt `build_persona` den Text:

1. **Spalten:** alle außer `prompt.exclude_profile_columns` (ID, `idno`, Gewichte, Stichprobendesign); leere Werte
   werden übersprungen. Nichts wird erfunden, eingesetzt werden nur Werte der Zeile und Labels aus dem Codebook.
2. **Elf thematische Absätze** ohne Überschriften (`PARAGRAPHS`): Person und Herkunft; Haushalt und Familie; Bildung
   und Arbeit; Einkommen, Partner*in, Eltern; Medien, Vertrauen, Politik; Zufriedenheit und Einstellungen;
   Wohlbefinden und soziales Leben; Religion und Diskriminierung; Klimawandel; Gesundheit und Lebensstil;
   Persönlichkeit, Geschlecht, Ansichten über Frauen und Männer.
3. **Satzvorlagen je Variable:** Text mit Platzhaltern (`{label}`, `{lc}`, `{value}`, `{scale}` mit Skalenenden,
   `{country}`), Zuordnung Code → Satz oder Funktion. Arbeitsbezogene Sätze im Präsens, wenn die Person in den letzten
   7 Tagen bezahlt gearbeitet hat, sonst im Präteritum.
4. **Zusammengehörige Variablen in einem Satz** (`Group`): `rated` (z. B. Vertrauen in sieben Institutionen),
   `did` (Ja/Nein-Listen wie politische Beteiligung), `listed` (Aufzählungen), `by_label` (gleiche Antworten bündeln,
   z. B. Depressionsskala), dazu eigene Funktionen für Haushalt, Herkunft, Religion, Alkohol, Klima, COVID usw.
5. **Codebook- und Erhebungssprache entfernt** („post-coded“, „not applicable is recorded“, Split-Ballot-Gruppen,
   „listed on the card“). Drei reine Kodiervariablen erzeugen keinen eigenen Satz (`admrclc`, `dscrnap`, `medtrnap`);
   doppelte Kodierungen werden zusammengefasst (`marsts`/`maritalb`, `mainact`/`mnactic`, `rlgdnm`/`rlgdnade`).
   Ergebnis: rund 2 560 statt rund 3 650 Wörter je Profiltext (nur „Who you are“, ohne übrigen System-Prompt),
   ohne Informationsverlust. Im Lauf: im Mittel 2 560 Wörter (min. 1 729, max. 2 721) aus im Mittel 196
   Variablen (min. 120, max. 216).
6. **Rückfall** für Variablen ohne Vorlage: `Asked about "<Codebook-Titel>", your answer was: <Label>.` Welche das
   betrifft, steht in `persona_stats.generic_sentences` im Log und in `run_report.md`.
7. **Test:** `tests/test_llm.py` stellt für die ersten 200 Personen sicher, dass jede nicht leere Variable
   verarbeitet wird und kein Rückfallsatz nötig ist. Für alle 2 262 Personen des Laufs weist `run_report.md` aus,
   dass keine Variable einen generischen Satz brauchte.

Beispiel `DE_50032` (Ausschnitt; 2 574 Wörter aus 201 Variablen, vollständig in
[`prompts/DE_50032.txt`](results/llm/claude-haiku-5-5_low_batch_all/prompts/DE_50032.txt)):

> You are a 42-year-old woman. You live in a country village in Bayern, Germany. You were born in Germany and are a
> citizen of Germany. […] You live in a household of 4 people: you, your partner (a man, born 1974), your daughter
> (born 2008) […]. On a scale from 0 (no trust at all) to 10 (complete trust), your trust is 4 in Germany's
> parliament, 8 in the legal system, 8 in the police […]

### 4.4 Aufbau des Prompts

Das Modell bekommt nur, was eine befragte Person auch hätte:

```
SYSTEM
  ├─ Situation
  ├─ # Who you are       narratives Profil (4.3)
  └─ # How to answer
        ├─ Anti-Varianzkollaps-Anweisung   (prompt.anti_collapse_instruction)
        └─ Verbalized Sampling             (prompt.verbalized_sampling, sonst direkte Antwort)
USER
  └─ leerer PVQ-21: Einleitung, Skala 1–6, Q1–Q21 (für alle Personen identisch)
+ JSON-Schema (Structured Outputs)
```

**Situation.**

> You are taking part in a face-to-face interview for a social survey. The interviewer is about to hand you a
> questionnaire. Who you are is described below, under "Who you are". Answer every question as this person, from
> your own life, experiences and views. There are no right, wrong or socially desirable answers.

Bewusst weggelassen sind Studienname, Forschungszweck, ESS-Variablennamen und jeder Hinweis auf ein Sprachmodell.
Grund ist Leakage: Modelle kennen veröffentlichte Umfrageergebnisse, und Anweisungen wie „You do not know official
statistics“ verhindern den Rückgriff nicht [Dalloul & Pfeifer 2026, S. 8, 10, 16]. Der Prompt gibt deshalb erst gar
keinen Hinweis auf die Studie; Schritt 8f prüft das automatisch. Unlearning, die dort wirksame Methode, braucht
Zugriff auf die Modellgewichte und ist mit einem API-Modell nicht möglich.

**Anti-Varianzkollaps-Anweisung (Experiment 2).**

> Answer exactly and without compromise as the person described. Do not give the answers an average person or a
> typical respondent would give, and do not soften your views towards the middle of the scale: where your views are
> strong, specific or unusual, your answers should show it.

Sie richtet sich gegen den Sog zum Mittelwert und den Typikalitäts-Bias und steht **nach** dem langen Profil, direkt
vor dem Fragebogen, damit sie nicht im Kontext untergeht. Abweichungen vom ursprünglichen Wortlaut (4.1):

- **Keine Fachbegriffe** wie „Varianzkollaps“, „Mode Collapse“ oder „KI-Assistent“. Sie würden verraten, dass es um
  ein Experiment über Sprachmodelle geht, und die Rolle brechen.
- **Kein Zwang zu Extremen.** Der ursprüngliche Wortlaut verlangte „ausschließlich die extremen, spezifischen und eckigen
  Ansichten“. Das hätte auch gemäßigte Personen zu Extremwerten gedrängt und Verbalized Sampling widersprochen, das
  echte Unsicherheit abbilden soll. Die Fassung oben verbietet nur das Abschwächen zur Mitte.

### 4.5 Technik 2: Verbalized Sampling

Anleitung im Prompt:

> For each question:
> 1. reasoning: In one or two sentences, in your own voice, think about what in your life and views makes the
>    description more or less like you.
> 2. probabilities: Give, for each of the six answer options, the probability (from 0.0 to 1.0) that you would choose
>    it. The six probabilities must add up to 1. Put most of the weight on one option if you are sure, and spread it
>    over several options if you are not.

Das JSON-Schema erzwingt je Frage `question`, `reasoning`, `probabilities` (`"1"`…`"6"`) in dieser Reihenfolge; ein
Feld für eine eigene Antwort gibt es nicht.

**Grundlage** [Zhang et al. 2026, Abschnitt 4.1]: Fragt man nach *einer* Antwort, liefert das Modell die
stereotypste. Fragt man nach einer *Verteilung*, kommt diese der des Basismodells nahe; der Druck zur einen typischen
Antwort fällt weg. Das braucht weder Training noch Logits und funktioniert mit API-Modellen.

**Variante VS-CoT** (Tab. 1, S. 5; höchste Diversität, S. 7): erst überlegen, dann die Verteilung. Die Begründung
steht **vor** den Wahrscheinlichkeiten, damit sie die Verteilung beeinflussen kann, statt sie nachträglich zu
rechtfertigen. Anders als im Paper sind die Kandidaten fest vorgegeben: die sechs Antwortoptionen.

**Das Programm zieht die Antwort, nicht das Modell.** Das entspricht „VS (Human, Probability)“ in der
Dialogsimulation von [Zhang et al. 2026] (Abschnitt 6; Tab. 15), wo die KS-Statistik gegenüber direktem Prompting von
0,390 auf 0,246 sinkt. Eine „finale Entscheidung“ des Modells, wie sie der ursprüngliche Plan vorsah (4.1), kommt im Paper nicht
vor und würde den Druck zur typischen Antwort zurückbringen. Mit der Ziehung antwortet eine Person mit 30 % auf
„Somewhat like me“ auch in etwa 30 % der Fälle so.

**Ziehungsregel** (reproduzierbar):

1. Je Person ein eigener Zufallsgenerator `numpy.random.default_rng([sampling_seed, crc32(id)])`; gleicher Seed und
   gleiche ID ergeben dieselbe Ziehung, unabhängig von Reihenfolge und Parallelität.
2. Je Frage in der Reihenfolge Q1–Q21 eine Zufallszahl *u* ∈ [0, 1).
3. Die normierten Wahrscheinlichkeiten teilen [0, 1) in sechs Intervalle (kumulierte Summen); gewählt wird die
   Option, in deren Intervall *u* fällt.

Beispiel `DE_50032`, Q1: p = (0.10, 0.45, 0.30, 0.10, 0.03, 0.02) → Obergrenzen 0.10, 0.55, 0.85, 0.95, 0.98, 1.0;
mit *u* = 0.4606 ist die Antwort **2** („Like me“). Log und Trace enthalten alle Zwischenschritte und zusätzlich den
Modus (wahrscheinlichste Option).

**Erwartungswert: eigene Erweiterung, nicht Teil von Verbalized Sampling.** [Zhang et al. 2026] werten nur
gezogene Antworten aus (Diversität, in der Dialogsimulation KS-Statistik und L1-Abstand der gezogenen Beträge).
Erwartungswerte über eine Bewertungsskala kommen dort nur in Anhang D.8.1 vor, zu einem anderen Zweck
(Typikalitäts-Bewertungen aus Logprobs, „continuous measurements rather than binary choices“). Die Auswertung nutzt
zusätzlich den Erwartungswert Σ k · pk je Frage, begründet aus zwei eigenen Überlegungen: Nach dem Satz von der
totalen Varianz besteht die Streuung der gezogenen Antworten aus den Unterschieden zwischen den Twins und dem Zufall
der Ziehung (4.7.4); und die Vergleichsgrößen der Auswertung (Mittelwert, Demografie-Mittelwert) sind selbst
Erwartungswerte, gegen die eine gezogene Antwort im Nachteil wäre (5.3).

**Schalter `prompt.verbalized_sampling`:**

- `true`: Das Modell gibt je Frage eine Verteilung über die sechs Optionen an, die Antwort wird wie oben gezogen.
  **Diese Einstellung nutzt der Hauptlauf.**
- `false`: Das Modell wählt direkt eine Option, ohne Verteilung und Ziehung (Vergleichsbedingung „Direct“).

### 4.6 Modellaufruf und Protokoll

`providers.AnthropicProvider.complete` sendet beide Prompts an die Messages API mit Modell, `max_tokens` und `effort`
aus der Config, `thinking` aus `model.thinking` (`adaptive` → das Modell darf vorher nachdenken, die
Zusammenfassung landet im Log; `disabled` → bei Haiku 5.5 nur bis `effort: high` erlaubt, bei Opus 5.5 gar nicht)
und dem JSON-Schema als `output_config.format`.

Mit `run.mode: batch` gehen dieselben Anfragen über die Message Batches API (`batch.py`: 50 % Rabatt, asynchron,
höchstens 24 h). Ergebnisse werden über `custom_id` (die Personen-ID) zugeordnet; ungültige Antworten kommen in
einen weiteren Batch, bis `run.max_attempts` erreicht ist. Ein abgebrochener Lauf setzt beim Neustart den offenen
Batch fort, statt ihn erneut zu bezahlen (die API hält Ergebnisse 29 Tage). Für Tests und kleine N bleibt der direkte
Aufruf sinnvoll.

Ergebnisordner eines Laufs (`results/llm/<lauf>/`):

| Datei | Inhalt |
|---|---|
| `fragebogen_LLM.csv`, `scores_LLM.csv` | finale Antworten der Twins (Format wie `ESS_fragebogen_DE.csv`) und ihre Scores |
| `antworten_LLM_detail.csv` | je Person und Frage: Begründung, Wahrscheinlichkeiten roh und normiert, Intervallgrenzen, Zufallszahl, Antwort, Modus |
| `prompts/<id>.txt` | gesendeter System- und User-Prompt (im Repository nur `DE_50032`, siehe `results/llm/README.md`) |
| `logs/<id>.json` | Anfrage, Hash; je Versuch Zeitpunkt, Dauer bzw. Batch-ID, Abbruchgrund, Tokens, **komplette API-Antwort unverändert**, Denk-Zusammenfassung, Prüffehler |
| `traces/<id>.md` | dasselbe lesbar, Schritt für Schritt vom Prompt bis zur gezogenen Antwort |
| `batches.jsonl`, `batches/<batch_id>.jsonl` | Protokoll jedes Batches und seine Rohergebnisse, sofort gespeichert |
| `run_report.md` | Prüfungen (Spalten, Werte, IDs, keine Leaks), Tokens und Kosten, Profillänge, erster Vergleich mit den echten Antworten |
| `run.log`, `config_used.yaml` | Konsolenausgabe, tatsächlich verwendete Einstellungen |
| `verteilungen_report.md`, `verteilungen_*.csv` | Analyse der Wahrscheinlichkeitsvektoren (4.7.4) |

Auswertung und Abbildungen liegen getrennt davon in `results/auswertung/<lauf>/` (Abschnitt 5.7).

### 4.7 Vorexperiment: Welches Modell und welcher Thinking-Modus?

Ziel: begründet festlegen, mit welchem Modell und welchen Einstellungen der PVQ-21 für alle Personen ausgefüllt wird.
Gemessen wurden Tokens, Kosten, Dauer und Qualität. Configs: [`config/vorexperiment_which_thinking_mode/`](config/vorexperiment_which_thinking_mode/),
Ergebnisse: `results/llm/vorexperiment_which_thinking_mode/`.

**Ergebnis:**

| Einstellung | Wert | Grund |
|---|---|---|
| Modell | `claude-haiku-5-5` | Kein Modell ist in allen Qualitätsmaßen besser: Opus liegt näher an der einzelnen Person, unterscheidet die Personen aber noch schwächer (4.7.3). Haiku kostet rund ein 38stel (4.7.2). |
| `effort` | `low` | gleiche Qualität wie `medium`, günstiger und schneller |
| `thinking` | `disabled` | bringt keine Verbesserung, verengt die Streuung eher; bei `low` mit `adaptive` denkt Haiku nur zufällig, `disabled` schließt Thinking sicher aus und hält die Bedingung für alle Personen gleich |
| Ausführung | Batch API | 50 % Rabatt; die Wartezeit spielt keine Rolle |

#### 4.7.1 Methodik und Versuchsplan

**Art der Studie.** Das Vorexperiment ist eine explorative Pilotstudie (Screening) vor dem Hauptlauf. Es prüft keine
Hypothesen statistisch, sondern tastet ab, ob sich die Einstellungen, vor allem die Thinking-Modi, in Kosten und
Qualität **merklich** unterscheiden. Daraus wird die Einstellung für den Hauptlauf begründet ausgewählt. Die Ergebnisse
werden deshalb deskriptiv berichtet (Mittelwerte, Spannen, Anteile), ohne Signifikanztests.

**Design.** Messwiederholung (within-subject): Dieselben Personen durchlaufen jede Bedingung, jede in einem eigenen
leeren Chat.

| Variablen | Ausprägungen |
|---|---|
| Unabhängige Variablen (Faktoren) | Modell (Haiku 5.5, Opus 5.5), `effort` (`low`, `medium`), `thinking` (`adaptive`, `disabled`) |
| Konstant gehalten | Prompt (4.1–4.6), JSON-Schema, Personen (die ersten 100 Zeilen des Profils), `max_tokens` 16 000, `sampling_seed` 42, bis zu 3 Versuche, kein Prompt-Caching |
| Abhängige Variablen: Aufwand | Input- und Output-Tokens, Kosten, Dauer je Aufruf (4.7.2) |
| Abhängige Variablen: Qualität | MAE, Streuung zwischen Personen, SD in der Verteilung (4.7.3); Form der Vektoren und Nähe zur Populationsverteilung (4.7.4) |

| # | Lauf | Frage | Config |
|---|---|---|---|
| A | Opus 5.5, `medium`, Thinking an, N = 10 | Was kostet das stärkste Modell je Person? | `opus.yaml` |
| B | Haiku 5.5, `medium`, Thinking an | Was kostet das günstigste Modell? | `haiku_n100.yaml` |
| C | Haiku 5.5, `low`, Thinking an | Was bringt weniger Denktiefe? | `haiku_low_adaptive.yaml` |
| D | Haiku 5.5, `medium`, Thinking aus | Was ändert sich ohne Thinking? | `haiku_medium_disabled.yaml` |
| E | Haiku 5.5, `low`, Thinking aus | Verliert die günstigste Einstellung an Qualität? | `haiku_low_disabled.yaml` |
| F | Opus 5.5, `low`, Batch API | Wie schneidet Opus bei denselben 100 Personen ab? | `opus_low_batch.yaml` |

Für Haiku ist das Design vollfaktoriell (2 × 2 aus `effort` × Thinking, Läufe B–E). Opus kommt als Vergleich hinzu
(A, F); ein volles 2 × 2 × 2 ist nicht möglich, weil sich Thinking bei Opus 5.5 nicht abschalten lässt. In F hat Opus
bei `low` aber tatsächlich nicht gedacht (keine Denkblöcke, `thinking_tokens` überall 0); F ist damit direkt mit E
vergleichbar. Umgekehrt hat Haiku in C trotz `adaptive` praktisch nicht gedacht (Output-Tokens wie E, 4.7.2).
**Nennenswert gedacht wird nur in B**; der eigentliche Vergleich Thinking an/aus ist damit B gegen D.

**Entscheidungsregel.** Qualität geht vor: Eine Einstellung scheidet aus, wenn sie in den Qualitätsmaßen merklich
schlechter ist. Bei vergleichbarer Qualität entscheiden die Kosten, danach die Reproduzierbarkeit. Weil es je
Bedingung nur einen Lauf gibt, ist die Schwankung von Lauf zu Lauf unbekannt. Als Maßstab für „merklich“ dient daher
die Spanne zwischen den inhaltlich ähnlichen Haiku-Bedingungen B–E (MAE 0,997–1,024, also ≤ 0,03). Unterschiede in
dieser Größenordnung gelten als nicht merklich. Opus und Haiku unterscheiden sich merklich, aber in entgegengesetzte
Richtungen (Opus besser im MAE, schlechter in der Streuung zwischen Personen, 4.7.3); keines ist eindeutig besser, also
entscheiden die Kosten.

**Entscheidungen und ihre Begründung.**

| Entscheidung | Begründung |
|---|---|
| **N = 100 je Bedingung** | Bewusst klein, aus Kostengründen und weil das Ziel nur ist abzutasten, ob ein merklicher Unterschied zwischen den Thinking-Modi besteht. Dafür reichen 100 Personen × 21 Fragen = 2 100 Antwortvektoren je Bedingung, um die Größenordnung der Kennzahlen zu bestimmen. Eine Power-Analyse gibt es nicht: Kleine Effekte werden nicht erkannt, das ist gewollt. Ein Unterschied, der bei N = 100 nicht sichtbar wird, rechtfertigt die Mehrkosten einer teureren Einstellung im Hauptlauf ohnehin nicht. Kosten: Haiku rund 0,17–0,23 $ je Lauf, Opus (F, Batch) rund 3,11 $. |
| **Opus-Lauf A nur N = 10** | Reine Kostenmessung, bevor entschieden wird, ob sich ein 100er-Lauf mit Opus lohnt (0,0655 $ je Person zum Standard-Tarif). Für Qualitätsaussagen ist N = 10 zu klein; A fehlt deshalb in 4.7.3 und 4.7.4. |
| **Opus-Lauf F mit `low` und Batch API** | Batch halbiert die Kosten. Mit `low` denkt Opus nicht und ist damit unmittelbar mit E vergleichbar. |
| **Dieselben Personen in allen Läufen** | Gepaarter Vergleich: Unterschiede zwischen den Personen fallen heraus, Unterschiede zwischen den Läufen gehen nur auf die Einstellung zurück. So genügt ein kleineres N als bei getrennten Stichproben. |
| **Die ersten 100 Zeilen statt Zufallsauswahl** | Einfachste reproduzierbare Auswahl. Nachteil: Die Stichprobe ist nicht zufällig gezogen. Ob die Kennzahlen trotzdem tragen, prüft der Hauptlauf (4.8): Sie übertragen sich, nur der MAE ist über alle Personen etwas höher. |
| **Derselbe Prompt in allen Läufen** | Nur so lässt sich ein Unterschied dem Modell bzw. der Einstellung zuschreiben. Der Prompt ist der des Hauptlaufs, damit das Ergebnis direkt übertragbar ist. |
| **`effort` nur `low` und `medium`** | Die beiden günstigsten Stufen. Höhere Stufen erzeugen mehr Output-Tokens; da schon `medium` gegenüber `low` keinen Qualitätsgewinn bringt, ist von höheren Stufen bei diesem Prompt kein merklicher Gewinn zu erwarten. |
| **`thinking` `adaptive` gegen `disabled`** | Kernfrage des Vorexperiments. `adaptive` lässt das Modell selbst entscheiden, ob es nachdenkt; `disabled` schließt das sicher aus. Nur der Vergleich beider zeigt, ob Nachdenken den Varianzkollaps verringert. |
| **`max_tokens` 16 000** | Großzügige Obergrenze, damit Denken und Antwort nie abgeschnitten werden. Ein Abbruch zählt als ungültige Antwort und würde die Bedingungen mit Thinking systematisch benachteiligen. |
| **Bis zu 3 Versuche je Person** | Einzelne ungültige Antworten sollen keine Personen aus dem Vergleich fallen lassen; alle Läufe enden mit vollständig N = 100. |
| **Fester `sampling_seed` 42** | Die Ziehung der finalen Antwort ist reproduzierbar und in allen Läufen gleich. |
| **Qualität auf der Verteilung, nicht auf der gezogenen Antwort** | Die Ziehung fügt Zufallsrauschen hinzu, das bei N = 100 Unterschiede zwischen den Einstellungen überdecken könnte. Erwartungswert und Vektor messen direkt, was das Modell ausgibt. |
| **Kein Prompt-Caching** | Kosten zu Listenpreisen, zwischen allen Läufen direkt vergleichbar; die Hochrechnung für den Hauptlauf ist damit eher zu hoch als zu niedrig. |
| **Ein Lauf je Bedingung, keine Tests** | Wiederholungen hätten die Kosten vervielfacht, ohne die Auswahl zu ändern, solange die Unterschiede klein bleiben. Mit einem Lauf je Bedingung und 21 voneinander abhängigen Antworten je Person wären p-Werte wenig aussagekräftig; deshalb gilt die Entscheidungsregel oben. |

**Grenzen.** Unterschiede um ± 0,03 sind nicht belastbar (Abschnitt 6). Vollfaktoriell ist nur der Haiku-Teil, und
echtes Nachdenken kommt nur in einem Lauf (B) vor. Die Ergebnisse gelten für diesen Prompt mit Verbalized Sampling;
mit einem anderen Prompt könnte Thinking anders wirken.

#### 4.7.2 Tokens, Kosten und Dauer

**Woher die Zahlen stammen.** Tokens aus dem Feld `usage` jeder API-Antwort (im Log, summiert über alle Versuche).
Kosten = Tokens × Listenpreis laut
[Anthropic-Preisseite](https://platform.claude.com/docs/en/about-claude/pricing):

| Modell | Input / 1 Mio. Tokens | Output / 1 Mio. Tokens | Batch Input | Batch Output |
|---|---|---|---|---|
| Claude Opus 5.5 | 4,00 $ | 20,00 $ | 2,00 $ | 10,00 $ |
| Claude Haiku 5.5 (Prompt ≤ 100 000 Tokens) | 0,10 $ | 0,50 $ | 0,05 $ | 0,25 $ |

Der längste Prompt hatte 12 826 Tokens. Denk-Tokens werden als Output abgerechnet. Dauer je Aufruf: `duration_s` im
Log (ab den Haiku-Läufen); im Batch gibt es nur die Dauer des ganzen Batches.

Mittelwerte je Person; A–E zum Standard-Tarif, F zum Batch-Tarif. Die letzte Zeile rechnet alle Läufe einheitlich
zum Batch-Tarif hoch.

| | A: Opus `medium` + Th. | B: Haiku `medium` + Th. | C: Haiku `low` + Th. | D: Haiku `medium` | **E: Haiku `low`** | **F: Opus `low`, Batch** |
|---|---|---|---|---|---|---|
| N | 10 | 100 | 100 | 100 | 100 | 100 |
| API-Aufrufe | 10 | 101 | 100 | 100 | 100 | 100 |
| Input-Tokens je Person | 6 634 | 6 618 | 6 554 | 6 553 | 6 553 | 6 554 |
| Output-Tokens je Person | 1 948 | 3 212 | 1 972 | 2 028 | 1 982 | 1 799 |
| **Kosten je Person** | 0,0655 $ | 0,00227 $ | 0,00164 $ | 0,00167 $ | **0,00165 $** | **0,0311 $** |
| Dauer je Aufruf (Spanne) | – | 13,0 s (7,9–29,9) | 8,1 s (7,1–12,4) | 8,6 s (7,4–18,2) | 8,1 s (7,0–9,2) | Batch: 82 min |
| Hochrechnung 2 262 Personen, Batch | 74,09 $ | 2,57 $ | 1,86 $ | 1,89 $ | **1,86 $** | **70,33 $** |

- **Opus kostet je Person rund 38-mal so viel wie Haiku** (Hochrechnung F gegen E, beide Batch-Tarif). Das liegt fast nur am
  Preis je Token; die Token-Mengen sind ähnlich.
- **Thinking kostet nur bei `medium` etwas:** B schreibt rund 1 200 Output-Tokens mehr als D (+36 % Kosten, +51 %
  Dauer). Bei `low` denkt Haiku auch mit `adaptive` praktisch nicht (C ≈ E); ob es denkt, entscheidet dann aber das
  Modell, nicht die Config.
- **Thinking macht die Laufzeit unberechenbarer** (B bis 29,9 s je Aufruf, E höchstens 9,2 s); B hatte als einziger
  Lauf einen Wiederholungsversuch.
- **Die API ist das Bottleneck.** In Lauf E entfallen über 98 % der Zeit auf das Warten auf Antworten (rund 2 000
  Output-Tokens bei etwa 250 Tokens/s). Mit 4 parallelen Anfragen bräuchten 2 262 Personen rund 81 min.
- **Batch-Dauer schwankt stark:** Der Opus-Batch mit 100 Anfragen brauchte 82 min, der Haiku-Hauptlauf mit 2 262
  Anfragen gut 7 min. Sie hängt von Auslastung und Modell ab, nicht von der Zahl der Anfragen.

#### 4.7.3 Qualität und Varianzkollaps

Gerechnet wird mit der Verteilung selbst (`antworten_LLM_detail.csv`), nicht mit der gezogenen Antwort, um das
Zufallsrauschen der Ziehung auszuschließen.

| Messgröße | Berechnung | Bedeutung |
|---|---|---|
| MAE | mittlerer Abstand zwischen Erwartungswert Σ k·pk und echter Antwort | Nähe zur einzelnen Person (Ebene 1) |
| Streuung zwischen Personen | je Frage SD der Erwartungswerte über alle Personen, gemittelt; beim Menschen dieselbe Rechnung mit den echten Antworten | Varianzkollaps: Je näher am Menschen, desto weniger Kollaps |
| SD in der Verteilung | SD der Verteilung einer Frage, gemittelt | Unsicherheit innerhalb einer Antwort |

| | B: `medium` + Th. | C: `low` + Th. | D: `medium` | **E: `low`** | **F: Opus `low`** | Mensch |
|---|---|---|---|---|---|---|
| MAE (kleiner = besser) | 1,022 | 1,024 | 1,020 | 0,997 | **0,881** | – |
| MAE wahrscheinlichste Option (Modus statt Erwartungswert, nur E und F berechnet) | – | – | – | 1,085 | **0,848** | – |
| Streuung zwischen Personen | 0,675 | 0,702 | 0,712 | **0,704** | 0,549 | **1,122** |
| SD in der Verteilung | 1,112 | 1,143 | 1,110 | 1,127 | 1,071 | – |

- **`effort` und Thinking ändern die Genauigkeit kaum** (alle MAE ≈ 1,0, Abstände ≤ 0,03, ein Lauf je Einstellung).
- **Thinking schwächt den Kollaps nicht ab, eher im Gegenteil:** Die geringste Streuung hat B (`medium` + Thinking).
- **Der Kollaps ist in allen Einstellungen deutlich:** Die Haiku-Twins streuen nur etwa 60 % so stark wie die echten
  Personen, die Opus-Twins knapp 50 %.
- **Opus liegt näher an der Person** (MAE −12 %) und trifft die Antwortverteilung der Population besser (4.7.4),
  **unterscheidet die Personen aber noch schwächer** (0,55 statt 0,70). Für Ebene 1 spricht das für Opus, für die
  Milieu-Struktur in Ebene 2 eher dagegen. Nach der Entscheidungsregel (4.7.1) ist damit keines der Modelle eindeutig
  besser, und die Kosten entscheiden für Haiku.

**Literatur zu Thinking.** Eine Studie, die Thinking-Budget, Persona-Umfragen und Varianzkollaps gemeinsam
untersucht, wurde nicht gefunden. Es gibt nur indirekte Hinweise. Bei [Zhang et al. 2026] profitieren größere Modelle
(Abschnitt 5.1) und Reasoning-Modelle (Abschnitt 6.1) stärker von Verbalized Sampling; verglichen werden dort jedoch
ganze Modelle, nicht Thinking an/aus beim selben Modell. [Yang et al. 2026] zeigen, dass lange Reasoning-Ketten die
Generierung auf Token-Ebene deterministischer machen. Ob sich das auf die Streuung über Personas überträgt, ist offen.
Die eigenen Daten zeigen dazu ein gemischtes Bild: In B, dem einzigen Lauf mit nennenswertem Denken, streuen die
Erwartungswerte zwischen den Personen am wenigsten (0,675 gegenüber 0,712 in D), die Vektoren selbst sind aber
vielfältiger (73,8 statt 52,3 verschiedene Vektoren je Frage, 4.7.4). Thinking verfeinert also die Zahlen, schiebt die
Schwerpunkte der Personen aber nicht auseinander; mit einem Lauf je Bedingung ist das nicht belastbar. Unabhängig vom
Thinking finden [Meister et al. 2025], dass Modelle eine Verteilung genauer beschreiben als aus ihr ziehen können. Das
stützt die Ziehung per Programm aus der verbalisierten Verteilung (4.5) und passt zum Befund, dass die
wahrscheinlichste Option selbst einen Kollaps erzeugt (4.7.4).

#### 4.7.4 Analyse der Wahrscheinlichkeitsvektoren

Code: [`distributions.py`](src/ess_pipeline/llm/distributions.py), Stufe `analyse`. Grundlage: die Läufe B–F,
zusammen 10 500 Vektoren. Zwei Fragen:

1. **Differenziert das Modell sinnvoll?** Kleine Modelle geben oft fast gleichförmige (0,2 / 0,2 / …) oder sehr
   scharfe (0,9 / 0,1) Vektoren aus; beides trüge keine Information über die Person.
2. **Erzeugt die Auswertung selbst einen Kollaps?** Wer nur die wahrscheinlichste Option nimmt, wirft die Unsicherheit
   weg.

| Messgröße | Berechnung |
|---|---|
| Entropie | H = −Σ pk log2 pk in Bit; 0 = sicher, 2,585 = Gleichverteilung |
| scharf / One-Hot / flach | max p ≥ 0,8 / ≥ 0,99 / Entropie ≥ 90 % der Gleichverteilung |
| eingipflig | steigt bis zu einem Gipfel und fällt danach (Plateaus erlaubt) |
| Schablonen-Vektoren | Anteil der Personen mit exakt demselben Rohvektor wie eine andere Person bei derselben Frage |
| JS-Divergenz | Jensen-Shannon (Basis 2; 0 = gleich, 1 = ohne Überlappung) |
| Wasserstein-1 | Abstand zweier Verteilungen auf der geordneten Skala, in Skalenpunkten |

**Form der Vektoren**

| N = 100 | B (Haiku) | C (Haiku) | D (Haiku) | E (Haiku) | F (Opus) |
|---|---|---|---|---|---|
| Entropie, Mittel (10.–90. Perzentil) | 2,04 (1,58–2,36) | 2,06 (1,65–2,37) | 2,02 (1,63–2,34) | 2,03 (1,63–2,36) | 2,04 (1,72–2,26) |
| höchste Wahrscheinlichkeit, Mittel | 0,382 | 0,380 | 0,389 | 0,388 | 0,380 |
| scharf (max p ≥ 0,8) | 0,5 % | 0,1 % | 0,1 % | 0,1 % | 0 % |
| flach | 15,8 % | 20,3 % | 13,3 % | 16,3 % | 2,8 % |
| eingipflig | 99,95 % | 100 % | 100 % | 100 % | 100 % |
| Rohwerte auf 0,05-Raster | 74,3 % | 64,4 % | 62,6 % | 62,9 % | 54,6 % |
| verschiedene Vektoren je Frage (von 100) | 73,8 | 53,2 | 52,3 | 55,3 | 72,4 |
| Personen mit Schablonen-Vektor | 41,9 % | 64,8 % | 64,3 % | 62,3 % | 43,0 % |

- **Weder gleichförmig noch scharf, fast immer eingipflig** mit rund 2 Bit Entropie (etwa vier gleich wahrscheinliche
  Optionen). Die Modelle verschieben den Schwerpunkt je Person, ändern aber kaum, wie sicher sie sind.
- **Viele Personen bekommen denselben Vektor:** In C, D und E (praktisch ohne Denken) teilen knapp zwei Drittel ihren
  Vektor bei einer Frage mit einer anderen Person. Haiku greift auf einen kleinen Vorrat gerundeter Muster zurück.
  Echtes Thinking (B) verfeinert die Zahlen, trennt die Personen aber nicht stärker (Streuung zwischen Personen in
  4.7.3 sogar am geringsten).

**Populationsebene: drei Lesarten.** Je Frage wird die Antwortverteilung der 100 echten Personen verglichen mit (a)
nur der wahrscheinlichsten Option, (b) dem Mittel der Vektoren, (c) der gezogenen Antwort.

| | Mensch | B (Haiku) | C (Haiku) | D (Haiku) | E (Haiku) | F (Opus) |
|---|---|---|---|---|---|---|
| JS (a) wahrscheinlichste Option | – | 0,086 | 0,092 | 0,105 | 0,111 | 0,092 |
| JS (b) Mittel der Vektoren | – | 0,059 | 0,056 | 0,052 | 0,052 | **0,031** |
| JS (c) gezogene Antwort | – | 0,066 | 0,057 | 0,053 | 0,055 | **0,037** |
| Wasserstein (c) | – | 0,521 | 0,499 | 0,482 | 0,472 | **0,336** |
| SD je Frage (a) | 1,116 | 0,948 | 0,985 | 0,971 | 0,974 | 0,746 |
| SD je Frage (c) | 1,116 | 1,297 | 1,331 | 1,313 | 1,321 | 1,200 |

Die SD des Menschen ist hier als Populations-SD gerechnet (ohne Bessel-Korrektur) und liegt deshalb leicht unter dem
Wert 1,122 in 4.7.3 (Stichproben-SD); beides beschreibt dieselben 100 Personen.

- **Die wahrscheinlichste Option erzeugt den Kollaps selbst:** Die Streuung fällt unter die der Menschen, der Abstand
  zur echten Verteilung verdoppelt bis verdreifacht sich. Die Pipeline zieht deshalb aus der vollen Verteilung.
- **Mit den vollen Vektoren streuen die Antworten sogar zu stark** (Haiku 1,30–1,36 statt 1,12).

**Woher die Streuung kommt** (Satz von der totalen Varianz: gesamt = zwischen Personen + innerhalb eines Vektors).
Lauf E: 0,704² + 1,127² = 1,77 → SD 1,33 (gemessen 1,32). Lauf F: 0,549² + 1,071² = 1,45 → SD 1,20 (gemessen 1,20).
**Bei Haiku stammen rund 72 % der Streuung aus der Unsicherheit innerhalb jeder Person, bei Opus rund 79 %.** Die
Population sieht breit genug aus, aber überwiegend durch Zufall der Ziehung, nicht durch personenbezogene
Information. Gegenmaßnahmen müssen daher an den Schwerpunkten der Personen ansetzen (Prompt, Profil, Modell), nicht
an der Breite der Verteilung.

### 4.8 Hauptlauf

Haiku 5.5, `effort: low`, ohne Thinking, Batch API, alle Personen. Config:
[`config/llm_experiment.yaml`](config/llm_experiment.yaml), Ergebnisse: `results/llm/claude-haiku-5-5_low_batch_all/`.

| | Wert |
|---|---|
| Batch | `msgbatch_016pYd4YywTSoJBt36bEfEZp` |
| Personen | 2 262 abgeschickt, 2 262 gültig, 0 Wiederholungen, 0 Fehler |
| Tokens | Input 14 893 457 (6 584 je Person), Output 4 496 273 (1 988 je Person) |
| **Kosten** | **1,869 $ gesamt**, 0,000826 $ je Person, Batch-Tarif in allen Antworten |
| **Dauer** | Batch 7,2 min, ganzer Lauf mit Scores, Abbildungen und Analyse 9,0 min |

| | Hauptlauf, 2 262 Personen | Vorexperiment E, 100 Personen | Mensch (alle) |
|---|---|---|---|
| MAE Erwartungswert ↔ echte Antwort | 1,063 | 0,997 | – |
| Streuung der Erwartungswerte zwischen Personen | 0,709 | 0,704 | 1,166 |
| JS-Divergenz je Frage (gezogen) | 0,044 | 0,055 | – |
| SD der gezogenen Antworten je Frage | 1,353 | 1,321 | 1,166 |
| JS-Divergenz bei nur wahrscheinlichster Option | 0,098 | 0,111 | – |
| Entropie je Vektor, Mittel | 2,035 Bit | 2,032 Bit | – |

Die Hochrechnung (1,86 $) hat sich bestätigt, und die Kennzahlen der 100 Pilotpersonen tragen auf die ganze
Stichprobe. Der MAE liegt über alle Personen etwas höher als bei den ersten 100.

Die Varianzzerlegung aus 4.7.4 bestätigt sich ebenfalls (Abbildung A2, `varianzzerlegung.csv`, Varianz je Frage
gemittelt): Personen 1,40, Twins zwischen den Erwartungswerten 0,57, durch die Ziehung 1,30. Nur rund 30 % der
Twin-Varianz unterscheiden die Twins voneinander, rund 70 % stammen aus der Ziehung.

---

## 5. Phase 4: Auswertung

Code: [`src/ess_pipeline/analysis/`](src/ess_pipeline/analysis/). Vergleicht die Twins eines Laufs mit ihren
Vorbildern, ohne das Modell erneut anzufragen. Deterministisch (Seed 42).

```bash
python run_llm.py --stages auswertung                                  # Hauptlauf
python -m ess_pipeline.analysis.forschungsfragen results/llm/<lauf>    # beliebiger Lauf -> results/auswertung/<lauf>/
```

| Datei | Aufgabe |
|---|---|
| `forschungsfragen.py` | Ablauf, Vergleichsgrößen, LPA (Milieus), Tabellen, Bericht |
| `forschungsfragen_plots.py` | eine Abbildung je Unterfrage |
| `ebene1.py` | MAE, Spearman je Zeile, Holm, Zufallspaarung, Item-Tabelle |
| `ebene2.py` | k-Means (nur Silhouette und Robustheit), Bures-Wasserstein, MMD, Split-Half |
| `data.py` | Mensch und Twin über die ID paaren, Subgruppen aus dem Profil |

**Ergebnis des Hauptlaufs:**
[`results/auswertung/claude-haiku-5-5_low_batch_all/report.md`](results/auswertung/claude-haiku-5-5_low_batch_all/report.md).

### 5.1 Herleitung der Metriken

Für jede Ebene wurden zuerst **vier Kategorien** festgelegt, die verschiedene, voneinander unabhängige Eigenschaften
messen, und dann je Kategorie eine Hauptmetrik gewählt. Ziel war ein vollständiges, aber nicht redundantes Set.

**Ebene 1: Wie nah ist jeder Twin an seiner Person?** Rohskala 1–6 (umgepolt), gepaart über die ID.

| Kategorie | Frage | Hauptmetrik | Begründung |
|---|---|---|---|
| Absolute Genauigkeit | Wie groß ist der Fehler? | **MAE** je Twin und global; RMSE ergänzend | Direkt lesbar: MAE 0,8 heißt „im Mittel 0,8 Skalenpunkte daneben“. RMSE bestraft große Ausreißer (Mensch 1, LLM 6) stärker |
| Profilähnlichkeit | Stimmt das relative Muster? | **Spearman ρ** über die 21 Items je Paar | Ein Twin kann das Niveau verfehlen (z. B. generell vorsichtiger antworten) und trotzdem die Rangfolge treffen („Sicherheit ist ihr wichtiger als Stimulation“). Spearman, weil die Skala streng genommen ordinal ist. Undefinierte ρ (alle Antworten gleich) sind ein Kollaps-Hinweis |
| Systematischer Bias | In welche Richtung geht der Fehler? | **Mean Error** (LLM − Mensch) je Item | Anders als beim MAE heben sich Über- und Unterschätzung auf. Ein ME von +1,5 bei einem Item heißt: Das LLM stimmt dort systematisch zu stark zu, statt zufällig zu streuen |
| Demografische Diskrepanz | Bei welchen Gruppen klappt es schlechter? | **MAE je Subgruppe**, geprüft mit ANOVA bzw. t-Test | Die Twin-MAEs nach Merkmalen gruppieren (z. B. 20–29 gegen 60–69 Jahre); der Test zeigt, ob das Gefälle signifikant ist |

**Ebene 2: Bildet die simulierte Population dieselben Werte-Milieus?** Raum: die 10 zentrierten Basiswerte.

| Kategorie | Frage | Hauptmetrik | Begründung |
|---|---|---|---|
| Lage | Wo liegen die Milieus? | **Euklidischer Abstand der Zentroide** je zugeordnetem Paar | Einfach und interpretierbar: Stimmt das typische Werteprofil eines Milieus überein? |
| Streuung | Wie breit sind sie? | **tr(Σ)**, die Summe der Varianzen, gezogen und mit Erwartungswerten; Bures-Wasserstein-Distanz der Kovarianzmatrizen nur als Zusatzzahl im Text | tr(Σ) beantwortet die Frage der Arbeit (gleich breit, und woher kommt die Breite?) in einer Zahl. Bures-Wasserstein vergleicht auch Richtung und elliptische Form (sie entspricht der Wasserstein-2-Distanz zentrierter Normalverteilungen). Ein Milieu kann gleich liegen, aber anders streuen, und umgekehrt. Prüft, ob das LLM die Vielfalt innerhalb eines Milieus abbildet oder unnatürlich homogen antwortet |
| Form | Wie sind die Punkte insgesamt verteilt? | **MMD** (RBF-Kern) über die ganze Population | Werte bilden selten perfekte Ellipsen; MMD vergleicht ganze Verteilungen ohne Annahme über ihre Form, auch Schiefe, Teilgruppen oder „bananenförmige“ Strukturen, und hat etablierte Zwei-Stichproben-Tests. Gleichwertige Alternative: Energy Distance |
| Zuordnung | Landen die Twins im selben Milieu? | **Adjusted Rand Index** | Misst, ob zwei Personen, die beim Menschen im selben Milieu sind, auch als Twins zusammen landen; „adjusted“ rechnet zufällige Übereinstimmung heraus. Braucht kein Matching der Cluster |

Würde man nur die Mittelpunkte vergleichen, bliebe unbemerkt, wenn das LLM viel einheitlicher antwortet (Streuung)
oder die Twins falsch zuordnet (Zuordnung). Zusammen zeigen die vier Kategorien, ob die KI-Milieus an derselben Stelle
liegen, gleich ausgedehnt sind, makroskopisch gleich geformt sind und mikroskopisch dieselben Personen gruppieren.

**Erweiterungen gegenüber dem Grundset.** Bei der Umsetzung kamen hinzu:

- **Vergleichsgrößen ohne Personenwissen** (5.3), weil ein MAE allein nicht sagt, *woher* die Nähe kommt. Das ist die
  eigentliche, schärfere Frage der Ebene 1.
- **Individuelle Abweichung** von ρ (früher „persönlicher Anteil“) und **Trennschärfe je Item** (1b, 1b′), weil das rohe
  ρ durch die gemeinsame Wertehierarchie aufgebläht ist.
- **Erwartungswert Σ k · pk** neben der gezogenen Antwort (4.5, 5.3) und die **Varianzzerlegung** (A2), weil rund
  70 % der Twin-Streuung aus der Ziehung stammen. Ebene 1 wird zusätzlich vollständig mit gezogenen Antworten
  gerechnet (**Sensitivitätsanalyse**, 5.6).
- **Varianzkollaps innerhalb der Demografie-Zellen** (1e) mit Bootstrap-Referenz.
- **Vorfrage 2.0**, ob es überhaupt Milieus gibt, und ein **Split-Half-Rauschniveau** als Nullwert für Lage,
  Streuung und Form.
- **Fazit 3:** Wie stark erklärt die Demografie die Werte bei Mensch und Twin?

Energy Distance ist nicht umgesetzt; MMD deckt dieselbe Frage ab.

### 5.2 Daten vorbereiten

1. **Paaren über die ID:** echte Antworten, Twin-Antworten und die Scores beider Seiten; nur Personen mit 21 gültigen
   Antworten auf beiden Seiten.
2. **Umpolen** (`x' = 7 − x`). Ein Fehler ist immer **LLM − Mensch**: positiv heißt, das LLM schreibt dem Wert mehr
   Wichtigkeit zu als die Person.
3. **Subgruppen** bilden (Übersicht unten).

**Subgruppen im Überblick.** Die Arbeit verwendet zwei Arten von Subgruppen, die auf unterschiedlichem Weg entstehen:

- **Vorab festgelegt (aus dem Profil):** Sechs demografische Merkmale, die im ESS-Profil jeder Person stehen und
  vor der Auswertung bestimmt wurden. Die Einteilung ist von Hand gesetzt (Grenzen und Zusammenfassung der
  ESS-Kategorien in [`data.py`](src/ess_pipeline/analysis/data.py), `SUBGROUPS`); sie hängt nicht von den Antworten ab.
- **In den Daten gefunden (aus den Antworten):** die zwei Werte-Milieus. Sie werden nicht vorgegeben, sondern per
  LPA aus den 10 zentrierten Basiswerten der *Personen* gebildet (5.5). Benannt sind sie nach ihrer Lage im Wertekreis:
  das Milieu mit der höheren Offenheit gegenüber Bewahrung heißt „offen“, das andere „bewahrend“.

| Art | Merkmal | Gruppen | Quelle (ESS-Variable) | N (Hauptlauf) |
|---|---|---|---|---|
| vorab festgelegt | Geschlecht | männlich / weiblich | `gndr` | 1 143 / 1 119 |
| vorab festgelegt | Alter | 15–29 / 30–44 / 45–59 / 60–74 / 75+ | `agea` | 408 / 514 / 546 / 569 / 220 |
| vorab festgelegt | Schulabschluss | niedrig (kein Abschluss, Hauptschule) / mittel (Realschule) / hoch (Fach-/Hochschulreife) | `edudde1` | 501 / 732 / 1 021 |
| vorab festgelegt | Wohnort | Großstadt (inkl. Vororte) / Kleinstadt / ländlich (Dorf, Einzelhof) | `domicil` | 690 / 719 / 852 |
| vorab festgelegt | Region | West / Ost (neue Bundesländer inkl. Berlin) | `region` | 1 862 / 400 |
| vorab festgelegt | Religion | religiös gebunden / nicht gebunden | `rlgblg` | 1 177 / 1 079 |
| in den Daten gefunden | Werte-Milieu | Milieu 1 (offen) / Milieu 2 (bewahrend) | LPA, k = 2 (5.5) | 1 253 / 1 009 |

Fehlende Angaben zählen in keiner Gruppe, deshalb summieren sich einzelne Zeilen nicht ganz auf N = 2 262.

**Wo welche Subgruppen verwendet werden:**

- **1d (Subgruppen):** alle sieben Merkmale in der ANOVA. In der Regression nur die sechs vorab festgelegten, weil das
  Werte-Milieu aus den Antworten der Person selbst gebildet ist, deren Fehler die Regression erklären soll.
- **Demografie-Zellen** (Demografie-Mittelwert in 5.3, Varianzkollaps 1e): die Kreuzung Geschlecht × Alter ×
  Schulabschluss, also eine Teilmenge der vorab festgelegten Merkmale.
- **Ebene 2 (2a–2d):** nur die Werte-Milieus, getrennt für Personen und Twins gebildet.
- **Fazit 3:** die sechs vorab festgelegten Merkmale als Erklärung der Werte und der Milieuzugehörigkeit.

### 5.3 Vergleichsgrößen: Woher kommt die Nähe?

Ein MAE allein sagt nicht, ob das LLM die *Person* kennt oder nur weiß, wie Deutsche typischerweise antworten. Jeder
Twin wird deshalb gegen Vorhersagen ohne Personenwissen verglichen:

| Vergleichsgröße | Was sie weiß | Frage | Rolle |
|---|---|---|---|
| **Zufallspaarung (fremder Twin)** | die LLM-Antworten einer *anderen* Person (20 Mischungen, niemand behält die eigenen) | Steckt etwas von dieser Person im Twin oder nur „wie LLM-Twins antworten“? | **Untergrenze**, in allen Ebene-1-Abbildungen |
| **Demografie-Zellmittel (Demografie-Mittelwert)** | mittlere Antwort der *anderen* Menschen gleichen Geschlechts, Alters und Abschlusses (leave-one-out) | Bringt das ganze Profil mehr als drei Merkmale? | **Messlatte**, in allen Ebene-1-Abbildungen |
| Mittelprofil (Mittelwert aller Personen) | ESS-Durchschnitt je Item | Schlägt der Twin das bloße Raten des Durchschnitts? | nur 1a, als anschaulicher Bezug |
| Zufall 1–6 | nichts (exakter Erwartungswert) | Ist der Twin besser als Würfeln? | nur Text und `kennzahlen.csv` |

**Warum zwei reichen.** Der fremde Twin teilt mit dem Twin Modell, Prompt und systematischen Fehler (1c); der
Unterschied ist genau die Wirkung des Profils. Der Demografie-Mittelwert ist, was eine Forscherin mit ESS-Daten ohne
LLM erreicht; er kennt nichts über die Person, aber die echten Antworten aller anderen Befragten, die dem Modell
fehlen. Das Mittelprofil ist ein Sonderfall davon (eine einzige Zelle) und liegt fast gleichauf; beim ρ der
individuellen Abweichung ist es per Definition null. Würfeln schlägt jedes sinnvoll antwortende Modell (99,9 % der
Twins) und trennt deshalb nichts.

**Datengrundlage: Erwartungswert auf Ebene 1, Ziehung auf Ebene 2.** Die Wahl folgt aus der Rolle der Daten auf
der jeweiligen Ebene, nicht aus den Ergebnissen:

- **Die Ziehung enthält keine zusätzliche Information.** Alles, was das Modell über die Person aussagt, steckt in den
  sechs Wahrscheinlichkeiten pk. Die gezogene Antwort ist eine Funktion dieser pk und einer Zufallszahl, die die
  Pipeline selbst erzeugt (4.5); sie fügt den pk nur Ziehungsrauschen hinzu.
- **Ebene 1 vergleicht Punktprognosen.** Für jede Person wird *ein* Wert je Frage mit ihrer Antwort verglichen. Die
  Vergleichsgrößen (Demografie-Mittelwert, Mittelwert aller Personen) sind Mittelwerte, also Erwartungswerte ohne
  Ziehungsrauschen. Die passende Punktprognose des Twins ist deshalb der Erwartungswert Σ k · pk; gegen eine gezogene
  Antwort trüge nur der Twin das Rauschen einer Ziehung. Der fremde Twin wird ebenfalls aus Erwartungswerten gebildet.
  Die Vorexperimente rechnen genauso (4.7.3, 4.8).
- **Ebene 2 braucht die Ziehungen.** Dort wird die synthetische Stichprobe als Datensatz mit der realen verglichen:
  Streuung, Form und Milieus einer Population entstehen aus einzelnen Antworten, nicht aus Erwartungswerten, die per
  Konstruktion enger streuen.

**Annahme: halbwegs kalibrierte Wahrscheinlichkeiten.** Der Erwartungswert ist nur dann eine gute Punktprognose,
wenn die verbalisierten pk die Unsicherheit über die Antwort der Person halbwegs richtig wiedergeben. Je Person lässt
sich das nicht prüfen, weil es nur eine echte Antwort je Frage gibt. Auf Populationsebene liegt das Mittel der Vektoren
nah an der echten Antwortverteilung (4.7.4, JS-Divergenz (b) 0,05). Dieselbe Analyse zeigt aber auch, dass die
gezogenen Antworten zu stark streuen (SD 1,30 statt 1,12); die Vektoren sind also eher zu flach. Die Annahme ist damit
plausibel, aber nicht belegt.

Beide Varianten stehen im Hauptteil dort nebeneinander, wo der Unterschied selbst der Befund ist (1a, 1e, A2, 2b,
Fazit 3). In Fazit 3 sind gezogene Antworten die untere Schranke (das Ziehungsrauschen ist von der Demografie nicht
erklärbar und drückt R²), Erwartungswerte die obere. **Ebene 1 wird zusätzlich vollständig mit gezogenen Antworten
gerechnet (Sensitivitätsanalyse, 5.6),** weil die Wahl eine Kernaussage verändert: die Rangfolge von Twin und
Demografie-Mittelwert bei der individuellen Abweichung (1b).

**Einschränkung.** Auch die Antworten der Personen sind eine einzelne, messfehlerbehaftete Antwort. Wo entrauschte
Twins mit Personen verglichen werden (1e, 2b, Fazit 3), überzeichnet das den Kollaps bzw. den Stereotyp-Abstand
etwas. In 1b trifft das Rauschen der Personen Twin und Vergleichsgröße gleich.

### 5.4 Ebene 1: Twin ↔ Person

Alle Rechnungen mit Erwartungswerten (5.3). Dieselben Rechnungen mit gezogenen Antworten stehen vollständig in der
Sensitivitätsanalyse (5.6); einzelne Werte zusätzlich in `kennzahlen.csv` und `twins.csv` (Spalten `…_gezogen`).

| Unterfrage | Rechnung | Warum |
|---|---|---|
| **A1** Beispielperson | 21 Antworten einer Person und ihres Twins (gezogen und Erwartungswert), drei Wahrscheinlichkeitsvektoren aufgeschlüsselt | Zeigt an einem Fall, woraus alle weiteren Kennzahlen bestehen |
| **1a** Genauigkeit | MAE je Twin (Erwartungswerte; gezogen als Zusatzmarker), RMSE, Anteil exakter Treffer (gezogen); Anteil Twins genauer als jede Vergleichsgröße; Wilcoxon Twin vs. Zufallspaarung; Robustheit: 20 neue Ziehungen aus denselben Wahrscheinlichkeiten | Wie weit liegt der Twin daneben, und ist das besser als ohne Personenwissen? |
| **1b** Profil | Spearman ρ über die 21 Items je Paar | Trifft der Twin die Rangfolge der Werte, unabhängig vom Antwortniveau? |
| **1b** individuelle Abweichung | ρ nach Abzug des Populationsmittels je Item; Wilcoxon (gepaart) gegen fremden Twin und gegen Zellmittel | Das rohe ρ ist aufgebläht, weil fast alle z. B. Wohlwollen hoch und Macht niedrig bewerten; erst nach Abzug bleibt das Persönliche (fremder Twin ≈ 0) |
| **A3** Fehler je Twin | je Person Differenz Twin − Vergleichsgröße derselben Person (MAE und ρ der individuellen Abweichung), gegen Demografie-Mittelwert und fremden Twin; der Anteil auf der guten Seite der 0 ist der Anteil Twins, die besser sind | Gibt es einzelne gute Twins, oder sind alle gleich mittelmäßig? |
| **1b′** Trennschärfe | Spearman ρ über Personen je Item, verglichen mit dem Zellmittel; gepaarter Bootstrap (1 000) für das Intervall von ρ und der Differenz Twin − Zellmittel („gesichert besser/schlechter“) | Unterscheidet das LLM die Personen innerhalb einer Frage besser als die Demografie? |
| **1c** Bias | Mean Error je Item mit 95-%-KI, t-Test gegen 0, Holm über 21 Items, Cohen's d; mittlerer ME aller Items als Referenzlinie (Antwortstil), Test gegen die Linie über die je Person zentrierten Fehler | Sind die Fehler gerichtet, und bei welchen Werten? |
| **A2** Varianzzerlegung | je Item Varianz der Erwartungswerte zwischen den Twins + mittlere Varianz innerhalb des Vektors (Satz von der totalen Varianz), gegen die Varianz der Personen | Wie viel der Twin-Streuung ist Information über die Person, wie viel Ziehung? |
| **1d** Subgruppen | MAE je Gruppe; ANOVA und Kruskal-Wallis auf dem Twin-MAE, η², Holm über die Merkmale; Regression MAE ~ die sechs demografischen Merkmale (ohne Werte-Milieu, weil es aus den Antworten der Person selbst gebildet ist; es steht nur in der ANOVA) | Trifft das LLM bestimmte Gruppen schlechter? |
| **1e** Varianzkollaps | SD je Item innerhalb der Demografie-Zellen (≥ 20 Personen), Mensch vs. Twin (gezogen und Erwartungswerte), Bootstrap-Band (1 000 Ziehungen, gleiches N) | Streuen Twins mit gleicher Demografie zu wenig? |

Im Bericht stehen 1b′, 1d und 1e im Anhang: Sie vertiefen 1a–1c, ändern aber die Antwort auf FF1 nicht.

### 5.5 Ebene 2: Population ↔ Population

Merkmalsraum: die 10 MRAT-zentrierten Basiswerte (Werteprofil ohne Antwortstil).

| Unterfrage | Rechnung | Warum |
|---|---|---|
| **2.0** Gibt es Milieus? | Silhouette von k-Means für k = 2…8, Mensch und Twin, gegen eine Normalverteilung gleicher Kovarianz *ohne* Cluster; zusätzlich gegen eine Normalverteilung mit der Kovarianz der Twins; BIC der LPA für k = 1…6; Silhouette der Twins zusätzlich mit Erwartungswerten und für die LPA-Lösung selbst | Bevor man Milieus vergleicht, muss klar sein, ob es sie gibt |
| Milieus bilden | LPA (Gauß-Mischung, diagonale Kovarianz) mit **k = 2** getrennt für Mensch und Twin, Zuordnung über Zentroide (Hungarian); k-Means als Robustheitsprüfung | Welches LLM-Milieu entspricht welchem menschlichen? |
| **2a** Lage | Euklidischer Abstand der Zentroide, Milieu-Anteile | Liegen die simulierten Milieus dort, wo die echten liegen? |
| **2b** Streuung | tr(Σ) je Seite, gezogen und mit Erwartungswerten; Bures-Wasserstein-Distanz der Kovarianzmatrizen nur im Text | Gleich breit, und woher kommt die Breite? |
| **2c** Form | MMD² (RBF-Kern, Median-Heuristik), Permutationstest (500) | Erfasst alle Verteilungsunterschiede, nicht nur Mittel und Varianz |
| **2d** Zuordnung | Adjusted Rand Index, Anteil Twins im Milieu ihrer Person gegen Zufallszuordnung; Robustheit mit Erwartungswerten (Jaccard je Milieu nur in `kennzahlen.csv`) | Landet der Twin dort, wo seine Person ist? |
| Rauschniveau | dieselben Kennzahlen zwischen zwei Zufallshälften der *menschlichen* Daten (Split-Half, 20 Wiederholungen) | Welchen Abstand erzeugt allein der Stichprobenzufall? |
| **Fazit 3** Werte oder Demografie | R² der Demografie für jeden Wert sowie x und y, Mensch vs. Twin (gezogen und mit Erwartungswerten) | Leitet das LLM Werte stärker aus der Demografie ab als echte Menschen (Stereotyp)? |

**Methode:** Die Milieus werden mit der LPA gebildet. k-Means dient nur der Prüfung, ob überhaupt eine Clusterstruktur
vorliegt (Silhouette in 2.0), und als Robustheitsprüfung der Zuordnung (2d).

**Einschränkung:** Die Silhouette der Menschen entspricht bei k = 2 der strukturlosen Normalverteilung. Die Werte
bilden ein Kontinuum, keine getrennten Gruppen; k = 2 ist fest gesetzt (`K` in `forschungsfragen.py`), die zwei
„Milieus“ sind als Regionen in diesem Kontinuum zu lesen.

### 5.6 Sensitivitätsanalyse: Ebene 1 mit gezogenen Antworten

Code: `ebene1_kern` und `sensitivitaet_ebene1` in [`forschungsfragen.py`](src/ess_pipeline/analysis/forschungsfragen.py).
Die Kernkennzahlen von 1a, A3, 1b, 1b′, 1c und 1d laufen durch **dieselbe Funktion**, einmal mit den Erwartungswerten
des Twins und einmal mit den gezogenen Antworten. Der fremde Twin wird jeweils aus derselben Variante gebildet, die
Vergleichsgrößen aus den Antworten der Personen bleiben gleich, Zufallspaarung und Bootstrap verwenden dieselben
Seeds. Die Variante mit Erwartungswerten ergibt deshalb exakt die Zahlen des Hauptteils (im Code geprüft). Dazu
kommen dieselben Kennzahlen für **20 neue Ziehungen** aus denselben pk, ohne neuen Modellaufruf. Sie zeigen, ob ein
Unterschied an der Wahl Erwartungswert/Ziehung liegt oder nur an der einen Ziehung des Laufs. Über die
Laufvariabilität des Modells (ein neuer Aufruf ergäbe andere pk) sagen sie nichts.

Im Report steht die Analyse als eigener Abschnitt im Anhang: alle Kennzahlen in beiden Varianten und eine Liste von
Aussagen mit der Angabe, ob sie von der Wahl abhängen.

**Ergebnis des Hauptlaufs** (N = 2 262; Spanne = Minimum bis Maximum über 20 neue Ziehungen):

| Unterfrage | Kennzahl | Erwartungswert | gezogen | Spanne neue Ziehungen |
|---|---|---|---|---|
| 1a | MAE Twin | 1,063 | 1,343 | 1,342–1,357 |
| 1a | MAE fremder Twin | 1,176 | 1,442 | 1,440–1,448 |
| 1a | MAE Demografie-Mittelwert | 0,924 | 0,924 | – |
| A3 | Anteil Twins genauer als Demografie-Mittelwert (MAE) | 25 % | 7 % | 6–8 % |
| 1b | ρ Profil Twin | 0,496 | 0,356 | 0,346–0,356 |
| 1b | ρ individuelle Abweichung Twin | **0,191** | **0,115** | 0,103–0,118 |
| 1b | ρ individuelle Abweichung Demografie-Mittelwert | **0,171** | **0,171** | – |
| 1b | ρ individuelle Abweichung fremder Twin | 0,001 | 0,000 | −0,001–0,002 |
| A3 | Anteil Twins mit ρ individuelle Abweichung > Demografie-Mittelwert | 51 % | 41 % | 39–42 % |
| 1b′ | Fragen mit ρ Twin > Demografie-Mittelwert (von 21) | 17 | 10 | 6–10 |
| 1b′ | davon gesichert besser / gesichert schlechter (Bootstrap) | 14 / 1 | 3 / 6 | – |
| 1c | ME gesamt | −0,301 | −0,305 | −0,309 bis −0,295 |
| 1c | Fragen mit gerichtetem Fehler (Holm), davon unterschätzt | 16, 14 | 16, 14 | 15–17, 13–14 |
| 1d | η² Schulabschluss | 0,039 | 0,025 | 0,019–0,040 |
| 1d | Regression MAE ~ Demografie, R² | 0,057 | 0,043 | 0,035–0,058 |

**Welche Aussagen hängen von der Wahl ab?**

| Aussage | Erwartungswert | gezogen | hängt ab |
|---|---|---|---|
| Der Twin ist genauer als ein fremder Twin (1a) | ja | ja | nein |
| Der Twin enthält Information über die Person, die individuelle Abweichung liegt über dem fremden Twin (1b) | ja | ja | nein |
| Der Twin ist beim MAE schlechter als der Demografie-Mittelwert, auch je Person (1a, A3) | ja | ja | nein |
| Die Fehler sind bei der Mehrheit der Fragen gerichtet, überwiegend nach unten (1c) | ja | ja | nein |
| Der Twin trifft die individuelle Abweichung mindestens so gut wie der Demografie-Mittelwert (1b) | ja | nein | **ja** |
| Die Mehrheit der Twins trifft die individuelle Abweichung besser als ihr Demografie-Mittelwert (A3) | ja | nein | **ja** |
| Der Twin trennt die Personen bei der Mehrheit der Fragen besser als der Demografie-Mittelwert (1b′) | ja | nein | **ja** |

**Lesart.** Von der Wahl hängt nur der Vergleich mit dem Demografie-Mittelwert bei Rangfolge und Trennschärfe ab
(1b, A3, 1b′): Mit Erwartungswerten liegt der Twin knapp vor dem Demografie-Mittelwert (0,19 gegen 0,17), mit
gezogenen Antworten deutlich dahinter (0,12). Das gilt in allen 20 neuen Ziehungen und liegt also an der Wahl, nicht
an der einen Ziehung. Im Text wird diese Aussage deshalb immer mit beiden Werten genannt. Alle anderen Aussagen der
Ebene 1 gelten in beiden Varianten. Der Mean Error (1c) ist in beiden Varianten in Erwartung gleich; MAE und ρ sind
mit gezogenen Antworten durchweg schlechter, weil das Ziehungsrauschen den Abstand vergrößert und die Rangfolge
verwischt. Der Varianzkollaps (1e, A2) wird ohnehin in beiden Varianten berichtet.

Der Vergleich mit gezogenen Antworten ist asymmetrisch: Nur der Twin trägt das Rauschen einer Ziehung, die
Vergleichsgrößen sind Mittelwerte. Er ist deshalb die strengere, nicht die fairere Variante.

### 5.7 Ausgabe

Im Ordner `results/auswertung/<lauf>/` (getrennt von den Rohdaten in `results/llm/<lauf>/`, weil jede Abbildung Mensch und Twin vergleicht):

| Datei | Inhalt |
|---|---|
| `report.md` | Datengrundlage und Vergleichsgrößen, Kurzantwort je Unterfrage, Abbildungen, Antwort auf die Hauptforschungsfrage; 1b′, 1d, 1e, 2c und die Sensitivitätsanalyse im Abschnitt „Anhang“ |
| `kennzahlen.csv` | alle Kennzahlen: Unterfrage, Kennzahl, Wert, Vergleich |
| `twins.csv` | je Twin: MAE, RMSE, ME, ρ, individuelle Abweichung (aus Erwartungswerten; `mae_gezogen`, `spearman_gezogen` … mit gezogenen Antworten), Vergleichsgrößen, Milieu von Person und Twin |
| `items.csv` | je Item: Mittel, SD, MAE, ME mit KI, d, t, p (Holm), ME zentriert mit p (Holm), Trennschärfe mit Bootstrap-Intervallen (Twin und Differenz zum Zellmittel) |
| `subgruppen.csv`, `subgruppen_tests.csv`, `regression_mae.csv` | 1d |
| `varianzkollaps.csv` | 1e |
| `varianzzerlegung.csv` | A2: je Item Varianz der Personen, zwischen den Twins, durch die Ziehung, Anteil zwischen den Twins |
| `milieus.csv`, `lpa_bic.csv` | 2.0–2c |
| `demografie_r2.csv` | Fazit 3: R² je Wert (Personen, Twins gezogen, Twins Erwartungswerte) und 95-%-Bootstrap-Intervalle der Faktoren |
| `sensitivitaet_ebene1.csv` | 5.6: Kernkennzahlen der Ebene 1 mit Erwartungswerten, gezogen und als Spanne über 20 neue Ziehungen |
| `sensitivitaet_aussagen.csv` | 5.6: je Aussage gültig mit Erwartungswerten / gezogen, Anteil der neuen Ziehungen, hängt von der Wahl ab |
| `figures/` | einziger Abbildungsordner der Auswertung: eine Abbildung je Unterfrage (`A1_beispielperson.png`, `FF1a_genauigkeit.png` … `Fazit3_werte_oder_demografie.png`; Titel, Dateiname und Report-Übersicht tragen dieselbe Nummer) |
| `figures/*.md` | ausführliche Plotbeschreibungen (von Hand geschrieben, nicht von der Pipeline erzeugt): verwendete Maße und warum, Lesehilfe, Kernerkenntnis. Zahlen beziehen sich auf den aktuellen Hauptlauf und müssen nach einer neuen Auswertung von Hand geprüft werden |

---

## 6. Grenzen und offene Punkte

**Reichweite der Ergebnisse.** Die Arbeit ist ein Proof of Concept für den Evaluationsrahmen (1.1). Alle Ergebnisse
der Auswertung beruhen auf

- **einem Modell** (Claude Haiku 5.5, `effort: low`, ohne Thinking). Opus 5.5 wurde nur im Vorexperiment an 100
  Personen geprüft (4.7) und verhält sich dort anders: genauer auf Ebene 1, aber mit schwächerer Unterscheidung der
  Personen. Auf andere Modelle lassen sich die Zahlen nicht übertragen.
- **einem Prompt-Design** (narratives Profil, Verbalized Sampling als VS-CoT, Anti-Varianzkollaps-Anweisung; 4.3–4.5).
  Andere Formulierungen, Profilformate oder Antwortformate können andere Twins ergeben.
- **einem Lauf.** Jede Person wurde genau einmal an das Modell geschickt. Wie stark sich die Wahrscheinlichkeiten pk
  und damit alle Kennzahlen bei einem erneuten Aufruf ändern würden (Laufvariabilität), ist nicht bekannt. Die 20
  neuen Ziehungen (1a, 2b, 5.6) erfassen nur den Zufall der Ziehung aus denselben pk, nicht diese Variabilität.

Weitere Modelle oder Läufe sind im Rahmen der Arbeit nicht vorgesehen.

**Kalibrierung der verbalisierten Wahrscheinlichkeiten.** Ebene 1 nimmt an, dass die pk halbwegs kalibriert sind
(5.3). Je Person ist das nicht prüfbar; die zu große Streuung der gezogenen Antworten (4.7.4) spricht eher für zu
flache Vektoren. Von der Wahl Erwartungswert/Ziehung hängt der Vergleich mit dem Demografie-Mittelwert bei Rangfolge
und Trennschärfe ab (5.6).

**Weitere offene Punkte:**

- **Experiment 1 (Base Model)** ist nicht umgesetzt. [Zhang et al. 2026] sehen die Ursache des Kollapses im
  Alignment, Basismodelle sind deutlich vielfältiger (S. 4). Ein Basismodell braucht aber ein anderes Prompt-Format
  (etwa ein Interview-Transkript zum Fortsetzen statt Chat mit JSON-Schema) und einen eigenen Anbieter in
  `providers.py`.
- **Kein Lauf ohne Anti-Varianzkollaps-Anweisung.** Alle Läufe verwenden `prompt.anti_collapse_instruction: true`.
  Ob die Anweisung die Twins weniger stereotyp macht (Bezug zu Fazit 3), lässt sich erst mit
  einem Vergleichslauf mit `false` beantworten; die Pipeline unterstützt das bereits.
- **Opus-Gesamtlauf** (ca. 70 $) ist nicht gemacht; der Modellvergleich beruht auf den 100 Personen der Läufe E und
  F. Da Opus auf Ebene 1 besser ist, die Personen aber schwächer unterscheidet, wäre der Vergleich über alle Personen
  eine mögliche Erweiterung über diese Arbeit hinaus.
- **Unlearning** nach [Dalloul & Pfeifer 2026] braucht Zugriff auf die Modellgewichte. Der Prompt begrenzt Leakage
  nur, indem er die Studie nicht nennt.
- **Ein Lauf je Einstellung** im Vorexperiment; Unterschiede in der Größenordnung ± 0,03 sind nicht belastbar.
- **Nachträgliches Schärfen der Vektoren** (pk^α neu normiert, α > 1) würde die Streuung innerhalb der Personen
  verringern, ist aber ein Eingriff in die Modellantworten, der eigens begründet und an getrennten Daten bestimmt
  werden müsste. An der Streuung zwischen den Personen ändert er nichts.
- **Datenfehler im Profil** werden unverändert übernommen, z. B. bei `DE_50032` ein Elternteil, der 2014 geboren sein
  soll.

---

## 7. Literatur

Verwendete Quellen (Volltexte nicht im Repository, Literaturverwaltung über Zotero):

- **[Dalloul & Pfeifer 2026]** Dalloul, A. & Pfeifer, M. (2026). *Can LLMs Mimic Household Surveys? From
  Representative Agents to Population Distributions.*
- **[Zhang et al. 2026]** Zhang, J., Yu, S., Chong, D., Sicilia, A., Tomz, M. R., Manning, C. D. & Shi, W. (2026).
  *Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity.* ICML 2026, arXiv:2510.01171v4.

Im Versuchsplan (4.1) genannt, im Text nicht weiter ausgewertet:

- Pfeifer, M. (2026). *Can LLMs Replace Survey Respondents? How unlearning fixes mode collapse in synthetic survey
  replies.* (Technik 3, Base Model)
- Moon, S., Abdulhai, M., Kang, M., Suh, J., Soedarmadji, W., Kohen Behar, E. & Chan, D. M. (2024). *Virtual Personas
  for Language Models via an Anthology of Backstories.* EMNLP 2024, arXiv:2407.06576. (Technik 1, narratives Profil)

Nur in 4.7.3 (Literatur zu Thinking) zitiert:

- **[Yang et al. 2026]** Yang, C., Li, S. & Holtzman, A. (2026). *LLM Probability Concentration: How Alignment Shrinks
  the Generative Horizon.* Transactions on Machine Learning Research (TMLR) 2026, arXiv:2506.17871 (Preprint 2025).
- **[Meister et al. 2025]** Meister, N., Guestrin, C. & Hashimoto, T. (2025). *Benchmarking Distributional Alignment of
  Large Language Models.* NAACL 2025, S. 24–49, doi:10.18653/v1/2025.naacl-long.2, arXiv:2411.05403 (Preprint 2024).
