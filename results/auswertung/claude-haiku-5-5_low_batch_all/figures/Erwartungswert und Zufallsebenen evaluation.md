# Erwartungswert und Zufallsebenen: Evaluation

Interne Bewertung der Abbildungen: Wo braucht es den Erwartungswert Σ k·pk, welche Vergleichsgrößen (Zufallsebenen)
haben eine eigene Daseinsberechtigung, und welche Auswahl ist die essenzielle. Zahlen aus dem Hauptlauf
`claude-haiku-5-5_low_batch_all` (N = 2 262); die bisher fehlenden Erwartungswert-Varianten sind probeweise
nachgerechnet und noch nicht in der Pipeline.

## Kurzfassung

- **Erwartungswert:** nötig, aber nicht als Zusatz in jeder Abbildung. Feste Regel: **Ebene 1 mit Erwartungswerten,
  Ebene 2 mit gezogenen Antworten**, beide Varianten nur dort, wo der Unterschied selbst der Befund ist (A2, 2b,
  Marker in 1a). Fazit 3 mit Erwartungswerten.
- **Verbalized-Sampling-Paper:** Der Erwartungswert ist dort keine Auswertungsgröße. Er ist eine eigene methodische
  Erweiterung und muss so begründet werden.
- **Vergleichsgrößen Ebene 1:** zwei reichen, der **fremde Twin** (Untergrenze: Weiß der Twin überhaupt etwas über die
  Person?) und der **Demografie-Mittelwert** (Messlatte: Weiß er mehr als drei Merkmale?). Zufall 1–6 streichen,
  Mittelwert aller Personen auf Text kürzen.
- **Ebene 2:** unverzichtbar sind die Zufallsdaten ohne Gruppen (2.0) und die Zufallszuordnung (2d). Jaccard streichen,
  Bures-Wasserstein und MMD in den Anhang, Rauschniveau behalten, aber als Signifikanz- und nicht als
  Relevanzmaßstab lesen.

## 1. Steht der Erwartungswert im Verbalized-Sampling-Paper?

Nein. Zhang et al. (2026) werten nur **gezogene** Antworten aus: Diversität der Texte und in der Dialogsimulation
KS-Statistik und L1-Abstand der gezogenen Spendenbeträge (Abschnitt 6, Tab. 15). „Expected values“ kommen nur in
Anhang D.8.1 vor: Typikalitäts-Bewertungen auf einer 1–10-Skala, „computed as expected values from logprob
distributions over rating tokens, providing continuous measurements rather than binary choices“. Das ist ein anderer
Zweck, taugt aber als Vorbild für Erwartungswerte über einer Antwortskala.

Begründung in der Arbeit deshalb aus eigener Logik:

1. **Satz von der totalen Varianz:** Varianz der gezogenen Antworten = Varianz der Erwartungswerte zwischen den Twins
   + mittlere Varianz innerhalb eines Vektors (Ziehung). Bei Haiku stammen rund 70 % aus der Ziehung (Doku 4.7.4).
2. **Fairness:** Die Vergleichsgrößen Mittelwert und Demografie-Mittelwert sind selbst Erwartungswerte (nicht
   ganzzahlig, ohne Ziehungsrauschen). Gegen die gezogene Twin-Antwort trägt nur der Twin Rauschen, das per
   Konstruktion keine Information über die Person enthält.

## 2. Zwei Lesarten des Twins

| | Gezogene Antwort | Erwartungswert Σ k·pk |
|---|---|---|
| Frage | Was bekommt jemand, der die synthetische Stichprobe benutzt? | Was weiß das Modell über die Person? |
| Gehört zu | Ebene 2 (Population als Datensatz) | Ebene 1 (Twin ↔ Person) |

**Regel:** Ebene 1 rechnet mit Erwartungswerten, Ebene 2 mit gezogenen Antworten. Einmal im Methodenteil begründen und
in jeder Fußzeile angeben („Datengrundlage: Erwartungswerte“ bzw. „gezogene Antworten“).

Gründe für Erwartungswerte in Ebene 1:

- **Fairness** gegenüber den Vergleichsgrößen (siehe 1.); der fremde Twin muss dann ebenfalls aus Erwartungswerten
  gerechnet werden.
- **Konsistenz mit der Doku:** 4.7.3 und 4.8 berichten MAE 1,063 und rechnen ausdrücklich „mit der Verteilung selbst“;
  1a zeigt bisher 1,34.
- **Die Aussage hängt daran** (Tabelle in 3.).

Beide Varianten nur dort, wo der Unterschied der Befund ist:

- **A2:** Die Zerlegung ist die Abbildung.
- **2b:** ×1,39 gezogen gegen ×0,61 mit Erwartungswerten, das ist die Kernaussage zum Kollaps.
- **1a:** gezogene Antwort als ein Zusatzmarker („was die Ziehung kostet: +0,28“).

## 3. Erwartungswert je Abbildung

| Abb. | Erwartungswert bisher drin? | Gezogen → Erwartungswert | Wichtig? |
|---|---|---|---|
| A1 | ja | MAE 1,00 → 0,86 | Ja: Ohne A1 versteht niemand Punkt und Ring in den anderen Abbildungen. |
| 1a | ja (Punkt) | MAE 1,34 → 1,06; Demografie-Mittelwert 0,92, Mittelwert 0,95 | Ja: Auch ohne Ziehung verliert der Twin beim MAE. |
| 1b | nein | ganzes Profil ρ 0,36 → **0,50** (Demografie 0,58); individuelle Abweichung 0,12 → **0,19** (Demografie 0,17) | **Ja, kippt:** „weniger, als Geschlecht, Alter und Bildung verraten“ stimmt bei der individuellen Abweichung nicht mehr. |
| 1b′ | nein | ρ je Frage 0,11 → **0,20** (Demografie 0,13); besser als Demografie bei **17 statt 10** von 21 Fragen | **Ja, kippt:** aus „nur schwach“ wird „schwach, aber besser als Demografie“. |
| 1c | nein | mittlerer Fehler in Erwartung identisch | Nein, ein Satz in der Beschreibung genügt. |
| 1d | nein | Gruppenunterschiede ändern sich kaum | Nein |
| 1e | ja | 21 von 21 Fragen unter dem Band der Personen | Ja, aber doppelt mit A2 |
| A2 | ist die Zerlegung selbst | – | Kernabbildung |
| A3 | nein | genauer als Mittelwert 10 % → **27 %**; als Demografie-Mittelwert 7 % → **25 %** | **Ja:** Antwort auf „Gibt es gute Twins?“ ändert sich deutlich. |
| 2.0 | nein | Silhouette Twins k = 2: 0,24 → **0,44** (Personen 0,16) | Ja: Die Aufspaltung der Twins wird viel stärker. |
| 2a, 2c | nein | Lage in Erwartung gleich, Form enger | Nein |
| 2b | ja | ×1,39 → ×0,61 | Ja, schon umgesetzt |
| 2d | nein | Treffer 62 % → 63 %, ARI 0,05 → 0,07 | Nein, aber als Satz: Die schlechte Zuordnung liegt nicht an der Ziehung. |
| Fazit 3 | nein | R² Twins z. B. Hedonismus 0,28 → **0,62**, Selbstbestimmung 0,11 → 0,40 (Personen 0,04–0,15) | **Ja, stärkster Effekt:** aus „bis zu viermal“ wird „bis zu zehnmal“. |

R² je Wert (Fazit 3), Personen / Twins gezogen / Twins Erwartungswert:

| Wert | Personen | gezogen | Erwartungswert |
|---|---|---|---|
| Selbstbestimmung | 0,043 | 0,105 | 0,401 |
| Stimulation | 0,090 | 0,301 | 0,578 |
| Hedonismus | 0,065 | 0,278 | 0,615 |
| Leistung | 0,077 | 0,112 | 0,360 |
| Macht | 0,064 | 0,077 | 0,296 |
| Sicherheit | 0,091 | 0,230 | 0,500 |
| Konformität | 0,072 | 0,254 | 0,537 |
| Tradition | 0,149 | 0,370 | 0,596 |
| Wohlwollen | 0,057 | 0,068 | 0,338 |
| Universalismus | 0,107 | 0,167 | 0,312 |

**Die Geschichte wird damit stimmiger:** Der Twin kennt die Rangfolge der Werte einer Person etwas besser als die
Demografie (1b, 1b′). Er verliert aber beim MAE, weil er systematisch falsch liegt (1c). Bei Spaß, Erfolg und
Kreativität unterschätzt er die Wichtigkeit, bei Regeln und korrektem Verhalten überschätzt er sie. Sein Wissen über
die Person ist dabei stark demografisch geprägt (Fazit 3).

**Einschränkung, die bisher nirgends steht:** Auch die Antworten der Personen sind eine einzelne verrauschte
„Ziehung“, denn der PVQ ist nicht perfekt reliabel.

- Bei 1e, 2b und Fazit 3 wird ein entrauschter Twin mit verrauschten Personen verglichen. Der Erwartungswert
  überschätzt deshalb Kollaps und Stereotyp-Abstand etwas.
- Formulierung: „gezogen = Vergleich Antwort gegen Antwort; Erwartungswert = Unterschiede zwischen den Twins ohne
  Ziehung, also eine untere Schranke.“
- Bei 1b und 1b′ trifft das Rauschen der Personen Twin und Vergleichsgröße gleich, dort ist der Vergleich fair.
- Bei Fazit 3 ist der Abstand so groß, dass er trotz dieser Einschränkung sicher bestehen bleibt.

## 4. Vergleichsgrößen Ebene 1

Prüffrage: Beantwortet die Vergleichsgröße eine eigene Frage, die keine andere schon beantwortet?

| Vergleichsgröße | Frage | Eigener Beitrag? | Urteil |
|---|---|---|---|
| **Fremder Twin** | Steckt im Twin etwas von *dieser* Person oder nur „wie das Modell generell antwortet“? | Ja, und als einzige. Twin und fremder Twin teilen Modell, Prompt und systematischen Fehler (1c); der Unterschied ist genau die Wirkung des Profils. Sauberster Kontrast der Arbeit. | **Behalten** |
| **Demografie-Mittelwert** | Ist der Twin besser als eine einfache statistische Schätzung? | Ja. Praxisnahe Messlatte: Wer ESS-Daten hat, kann ohne LLM so schätzen. Hängt direkt an Fazit 3. | **Behalten** |
| Mittelwert aller Personen | Ist der Twin besser als den Durchschnitt zu raten? | Kaum. Sonderfall des Demografie-Mittelwerts (eine einzige Zelle), fast gleichauf (0,95 gegen 0,92). Beim ρ der individuellen Abweichung per Definition null, taugt nur für den MAE. | **Auf Text kürzen** oder höchstens in 1a lassen (für Leser am anschaulichsten) |
| Zufall 1–6 | Ist der Twin besser als Würfeln? | Nein. Das schafft jedes Modell, das sinnvoll antwortet (99,9 % der Twins). Trennt nichts und lässt den Twin in 1a besser aussehen, als er ist. | **Aus den Abbildungen streichen**, höchstens ein Halbsatz |

**Rahmung des Demografie-Mittelwerts:** „ohne Wissen über die Person“ stimmt, aber er hat Wissen, das der Twin nicht
hat: die echten Antworten aller anderen Befragten (leave-one-out). Das ist kein Fehler, sondern die Aussage. Der Twin
bekommt mehr Information über die Person (das ganze Profil) und weniger über die Population. In einem Satz so
hinschreiben, sonst wirkt der Vergleich unfair.

**Übrig bleibt ein Rahmen aus zwei Grenzen:**

- Untergrenze, der fremde Twin: Weiß der Twin *überhaupt* etwas über die Person?
- Messlatte, der Demografie-Mittelwert: Weiß er *mehr als drei Merkmale*?

Jede Ebene-1-Abbildung braucht genau diese zwei Vergleiche, nicht mehr.

## 5. Vergleichswerte Ebene 2

| Vergleichswert | Wozu | Urteil |
|---|---|---|
| **Zufallsdaten ohne Gruppen (2.0)** | Ohne ihn ist die Silhouette nicht deutbar. Erst er zeigt: Personen bilden ein Kontinuum, die Twins spalten sich. | **Unverzichtbar** |
| **Zufallszuordnung 49 % (2d)** | Macht aus „62 % Treffer“ erst „kaum besser als Zufall“. | **Unverzichtbar** |
| ARI | Dieselbe Aussage, um Zufall bereinigt | Behalten als eine Zahl, ohne Erklärungsabsätze |
| Jaccard je Milieu | Wiederholt die Zeilenprozente der Tafel | **Streichen** |
| Rauschniveau Split-Half (2a, 2b, 2c) | Maßstab für Abstände ohne natürliche Einheit | Behalten, aber richtig einordnen (unten) |
| Bures-Wasserstein (2b) | Ob die Zusammenhänge zwischen den Werten gleich sind | Beantwortet eine Frage, die die Arbeit nicht stellt. **Anhang** |
| MMD mit Permutationstest (2c) | Unterschied der ganzen Verteilungen | Bei N = 2 262 ist p ≤ 0,002 praktisch garantiert; 2a und 2b sagen schon alles. **Anhang** |
| Bootstrap-Band (1e) | Signifikanz der SD-Unterschiede | Bei dieser Stichprobengröße winzig. Mit 1e in den Anhang |

**Einordnung des Rauschniveaus:** Bei 2 262 Personen ist es so klein, dass jeder Unterschied darüber liegt. Es zeigt,
dass ein Unterschied *echt* ist, nicht dass er *groß* ist. Für 2a wäre ein inhaltlicher Maßstab aussagekräftiger:
der Abstand zwischen Milieu 1 und Milieu 2 der Personen. Wenn die Twins um ungefähr den Abstand zweier Milieus
verschoben sind, versteht das jeder sofort. Der Wert ist noch nicht gerechnet; die Zentroide liegen vor.

## 6. Essenzielle Auswahl der Abbildungen

**Haupttext (10):**

| Abb. | Vergleiche darin |
|---|---|
| A1 | Erwartungswert und Ziehung erklärt, ohne Vergleichsgrößen |
| 1a | Twin (Erwartungswert) + Marker für die gezogene Antwort; fremder Twin, Demografie-Mittelwert (Mittelwert optional) |
| 1b | nur die individuelle Abweichung als Hauptaussage; Twin gegen Demografie-Mittelwert; fremder Twin ≈ 0 als Satz statt als leerer Balken |
| 1c | ohne Vergleichsgröße (mittlerer Fehler für beide Varianten gleich) |
| A3 | nur „genauer als der Demografie-Mittelwert“ und „genauer als der fremde Twin“ statt vier Anteilen |
| A2 | Kernabbildung zum Kollaps |
| 2.0 | Zufallsdaten ohne Gruppen |
| 2a | Personen gegen Twins, Maßstab Milieuabstand |
| 2b oder 2d | 2b für die Breite, 2d für die Zuordnung (mit Zufall 49 %) |
| Fazit 3 | Personen gegen Twins (Erwartungswerte) |

**Anhang oder ein Satz im Text:**

- **1b′:** Mit Erwartungswerten interessant (bei welchen Themen der Twin die Demografie schlägt), dupliziert aber
  teilweise 1b. Anhang, oder 1b ersetzen, wenn die Themen wichtiger sind.
- **1d:** Unterschiede höchstens 0,08 Punkte; „kaum“ passt in einen Satz.
- **1e:** A2 zeigt dasselbe direkter.
- **2c:** laut interner Notiz ohnehin erster Kandidat für den Anhang.

## 7. Weitere Punkte an den Abbildungen

1. **Uneinheitliche Prozentzahlen:** A2 sagt „33 % stärker“ (Varianz je Frage), 2b „39 %“ (Summe über die 10 Werte).
   Zwei verschiedene Größen, eine Fußnote muss das erklären.
2. **2b-Untertitel:** „39 % mehr … 39 % weniger“ ist ein Zufall der Zahlen und verwirrt. Besser: „×1,39 gezogen,
   ×0,61 mit Erwartungswerten“.
3. **1b′:** Nachrechnung ergibt 10 statt 8 Fragen besser als Demografie (Spearman je Frage). Prüfen, ob die Abbildung
   anders rechnet (andere Korrelation oder andere Behandlung von Bindungen).
4. **A1:** Legende „▲ rechts“ ist kryptisch; besser „▲ = Antwort der Person (rechte Felder)“.
5. **2d:** Die Farbskala ist bei vier Zellen mit Prozentzahlen überflüssig.

## 8. Abwägung

Die Umstellung von Ebene 1 auf Erwartungswerte ändert Kopfzahlen und Untertitel: 1a wird zu 1,06, 1b kippt zugunsten
des Twins, in A3 sind 25 % statt 7 % besser als der Demografie-Mittelwert. Das ist Arbeit, macht die Arbeit aber in
sich stimmig, mit 4.7.3/4.8 und mit fairen Vergleichen.

Alternative: bei gezogenen Antworten bleiben und den Erwartungswert nur als Robustheitsprüfung nennen. Dann muss
erklärt werden, warum der Twin mit einem Nachteil gegen Vergleichsgrößen antritt, die diesen Nachteil nicht haben.
Das ist schwerer zu verteidigen.

## To-do

- [x] Ebene 1 auf Erwartungswerte umstellen (`le` aus `expected_answers`, schon in `forschungsfragen.run`)
- [x] Fremden Twin aus Erwartungswerten rechnen (`per_person_shuffle(h, le, …)`)
- [x] 1b und 1b′ mit `rowwise_spearman(h, le)`, `deviation_spearman(h, le)` und ρ je Frage aus `le`
- [x] A3 mit Erwartungswerten, nur zwei Anteile (Demografie-Mittelwert, fremder Twin)
- [x] Fazit 3: R² aus `value_scores(le)` ergänzen, Hinweis auf Reliabilität der Personen
- [x] 2.0 und 2d: Erwartungswert-Ergebnis als ein Satz (Bericht und Beschreibungen)
- [x] Zufall 1–6 aus 1a und A3, Jaccard aus 2d entfernen (bleiben in `kennzahlen.csv`)
- [x] 2a: Abstand der beiden Personen-Milieus als Maßstab (Untertitel)
- [x] 1d, 1e, 1b′, 2c in den Anhang von `report.md`; Bures-Wasserstein nur im Text
- [x] Doku 4.5, 5.3, 5.4: Erwartungswert als eigene Erweiterung begründen, nicht als Teil von Verbalized Sampling
- [x] Untertitel 1a, 1b, 1b′, A3, Fazit 3 an die neuen Aussagen anpassen
- [x] Abschnitt 7: A1-Legende, 2b-Untertitel (× statt %), Fußnote A2/2b, Farbskala 2d entfernt

## Ergebnis der Umsetzung (Abweichungen von der Vorab-Rechnung)

- **Fremder Twin wird stärker:** Aus Erwartungswerten liegt er bei MAE 1,18 (gezogen 1,44) und ρ ganzes Profil 0,40
  (gezogen 0,28). Der Abstand Twin – fremder Twin bleibt gesichert (74 % der Twins genauer, p < 0,001).
- **1b′ hatte einen Zuordnungsfehler:** Der Demografie-Mittelwert je Frage wurde in Fragebogen-Reihenfolge den Items
  in anderer Reihenfolge gegenübergestellt. Behoben; daher 10 statt 8 Fragen (gezogen) bzw. 17 (Erwartungswerte).
- **1d:** Mit Erwartungswerten ist zusätzlich das Alter signifikant (75+ am ungenauesten), und Ost bleibt auch in der
  Regression signifikant. Alle Effekte bleiben klein (höchstens 0,09 Punkte).
- **Fazit 3:** bis 9,5-mal (Hedonismus), gezogen bis 4,3-mal.

## Prüfung auf Rechenfehler

Unabhängig nachgerechnet (eigene Implementierung direkt aus den Rohdateien): Ziehung und Erwartungswerte, MAE,
RMSE, alle Vergleichsgrößen, ρ (Profil, individuelle Abweichung, je Frage), ME mit t-Test, Holm und Cohens d,
Subgruppen-ANOVA und η², Within-Cell-SD, Varianzzerlegung, Wertescores, Zentroid-Abstand, tr(Σ),
Bures-Wasserstein (gegen scipy), Silhouette, Treffer und ARI, R² der Demografie. Alles stimmt überein.

Gefunden und behoben:

- **Gleitkomma-Bindungen:** Mathematisch gleiche Erwartungswerte (z. B. 4,55) unterschieden sich in der 16. Stelle
  und galten in Rangkorrelationen nicht als gebunden. Erwartungswerte und Demografie-Mittelwerte werden jetzt auf
  9 Stellen gerundet. Wirkung klein (ρ Profil 0,4961 → 0,4962). In 1b′ liegen „reich sein“, „Spaß haben“ und
  „Freunden loyal“ praktisch gleichauf mit dem Demografie-Mittelwert; das steht jetzt im Bericht.
- **Zwei verschiedene Anteile „besser als fremder Twin“:** 1a nannte 74 % (Mittel über 20 Zufallspaarungen), A3 65 %
  (eine Paarung). A3 nutzt jetzt ebenfalls das Mittel über 20 Paarungen; das Histogramm zeigt weiter eine Paarung.
- **Zuordnungsfehler in 1b′** (siehe oben) und ein nicht ersetzter Platzhalter im Bericht.
