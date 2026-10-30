# 2c – Haben die Verteilungen dieselbe Form?

Datei: `FF2c_form.png`

Abbildung 2a hat die **Mittelpunkte** verglichen, 2b die **Breite**. Zwei Verteilungen können aber in beidem übereinstimmen und sich trotzdem unterscheiden: Die eine kann schief sein, die andere symmetrisch; die eine kann einen Gipfel haben, die andere zwei.

Die Abbildung zeigt deshalb die **ganze Verteilung** jedes Werts, also wie viele Personen bzw. Twins welche Ausprägung haben.

## Welche Maße verwendet werden und warum

**Histogramm.** Für jeden der 10 zentrierten Werte wird gezählt, welcher Anteil der Personen bzw. Twins in welchem Wertebereich liegt.

*Warum?* Das Histogramm macht die Form einer Verteilung sichtbar: Lage, Breite, Schiefe und Gipfel auf einen Blick.

**MMD (Maximum Mean Discrepancy).** Die MMD misst, wie gut man zwei Punktwolken auseinanderhalten kann. Vereinfacht: Für jedes Paar von Punkten wird eine Ähnlichkeit berechnet, die mit wachsendem Abstand abnimmt. Dann wird verglichen, ob Personen untereinander, Twins untereinander und Personen mit Twins gleich ähnlich sind. Sind die beiden Verteilungen gleich, ist die MMD (genauer MMD²) nahe 0.

*Warum die MMD?* Die Histogramme zeigen jeden Wert einzeln. Die MMD prüft alle 10 Werte **zusammen**. Sie macht außerdem **keine Annahme über die Form** der Verteilung. Sie erkennt Unterschiede in Lage und Breite, aber auch Schiefe, mehrere Gipfel oder ungewöhnliche Formen, die Mittelwert und Varianz übersehen würden. Damit ergänzt sie 2a und 2b.

**Permutationstest.** Die Bezeichnungen „Person“ und „Twin“ werden 500-mal zufällig vertauscht, und jedes Mal wird die MMD berechnet. Wären Personen und Twins in Wahrheit gleich verteilt, spielte das Vertauschen keine Rolle, und der echte Wert läge mitten unter den vertauschten. Der Anteil der Vertauschungen mit einem mindestens so großen Wert ist der p-Wert.

*Warum?* Ein MMD-Wert wie 0,0585 ist für sich genommen schwer zu deuten. Der Permutationstest hat dieselbe Aufgabe wie der t-Test in 1c, braucht aber keine Annahme über die Verteilung.

## Was die Abbildung zeigt

**Jedes Feld** zeigt einen Wert. **Die x-Achse** ist die zentrierte Wichtigkeit (0 = persönlicher Durchschnitt), **die y-Achse** der Anteil. **Die blaue Stufenlinie** ist die Verteilung der Personen, **die orange** die der Twins; **die Mischfarbe** zeigt die Überlappung. **Die gestrichelten Linien** sind die Mittelwerte, **die graue senkrechte Linie** die 0.

**Die Verteilungen unterscheiden sich gesichert.** MMD² = 0,0585; **keine** der 500 Vertauschungen ergab einen so großen Wert, also **p ≤ 0,002** (der kleinste mit 500 Vertauschungen mögliche p-Wert). Zwischen zwei Zufallshälften der Personen liegt die MMD bei praktisch 0. Auch innerhalb jedes Milieus ist p ≤ 0,002.

- **Hedonismus und Leistung nach links verschoben:** Die Twins halten diese Werte für unwichtiger. Bei Hedonismus fehlt den Twins der deutliche Gipfel der Personen knapp über 0.
- **Konformität nach rechts verschoben:** Bei den Personen liegt der Gipfel unter 0, bei den Twins über 0. Das ist der auffälligste Unterschied.
- **Wohlwollen und Universalismus leicht nach rechts verschoben**; die Twins sind hier weniger stark auf einen Gipfel konzentriert.
- **Tradition und Sicherheit:** Die Mittelwerte stimmen fast überein, die Twin-Verteilungen sind aber **breiter und flacher**.
- **Macht** stimmt am besten überein, Selbstbestimmung und Stimulation weichen nur leicht ab.

**Was die Abbildung aussagt:** Die simulierte Population ist **nicht nur verschoben und breiter, sondern anders geformt**. Die Verschiebungen wiederholen das Muster aus 1c und 2a: Hedonismus und Leistung unterschätzt, Konformität überschätzt. Die Twin-Verteilungen sind fast überall breiter; das passt zu 2b und stammt überwiegend aus dem Auslosen der Antworten.

**Kernerkenntnis – der Bias betrifft die ganze Verteilung:** Die Abweichungen liegen nicht an einzelnen Ausreißern, sondern verschieben die ganze Verteilung. Wer mit den Twins statt mit echten Menschen arbeitet, würde zum Beispiel schließen, dass Konformität den meisten Deutschen überdurchschnittlich wichtig ist. Bei den echten Befragten ist es umgekehrt.

**Einschränkung:** Bei 2 262 Personen erkennt ein Test auch kleine Unterschiede als signifikant. Der p-Wert sagt deshalb nur, *dass* sich die Verteilungen unterscheiden, nicht *wie stark*. Wie stark, zeigen die Histogramme sowie 2a und 2b. Die Twin-Werte beruhen auf den gezogenen Antworten.

*N = 2 262 Personen, 10 zentrierte Werte aus gezogenen Antworten. MMD² mit RBF-Kern (Bandbreite nach Median-Heuristik) über alle 10 Werte gemeinsam, gesamt und je Milieu; Permutationstest mit 500 Vertauschungen.*
