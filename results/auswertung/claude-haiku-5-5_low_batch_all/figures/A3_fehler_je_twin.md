# A3 – Gibt es einzelne gute Twins?

Datei: `A3_fehler_je_twin.png`

Die Abbildungen 1a und 1b zeigen Mittelwerte über alle 2 262 Twins. Ein Mittelwert kann zweierlei verdecken: Entweder sind alle Twins gleich mittelmäßig, oder es gibt einige sehr gute und einige sehr schlechte.

Die Abbildung zeigt deshalb für **jede Person einzeln**, ob ihr Twin besser ist als die Vergleichsgrößen derselben Person.

## Welche Maße verwendet werden und warum

**Differenz je Person.** Für jede Person wird der Fehler ihres Twins mit dem Fehler ihres Demografie-Mittelwerts verglichen (links: MAE des Twins minus MAE des Demografie-Mittelwerts; rechts: ρ des Twins minus ρ des Demografie-Mittelwerts). Dasselbe geschieht mit dem fremden Twin.

*Warum die Differenz?* Twin und Vergleichsgröße beziehen sich auf **dieselbe** Person. Manche Personen sind leicht vorherzusagen, andere schwer; diese Schwierigkeit hebt sich in der Differenz auf. Der Anteil der Personen auf der „guten“ Seite der 0 ist dann direkt der Anteil der Twins, die besser sind. Eine frühere Fassung zeigte die Verteilung des MAE mit einer Linie beim *mittleren* Demografie-Mittelwert; daran ließ sich dieser Anteil nicht ablesen.

**Linkes Feld: MAE** (siehe 1a). **Links der 0** ist der Twin genauer.

**Rechtes Feld: ρ der individuellen Abweichung** (siehe 1b), also die Rangkorrelation nach Abzug des Mittelwerts je Frage. **Rechts der 0** ist der Twin besser.

**Fremder Twin.** Der Twin einer zufällig gewählten anderen Person, gemittelt über 20 Zufallspaarungen je Person wie in 1a.

## Was die Abbildung zeigt

**Orange** ist die Verteilung der Differenz zum Demografie-Mittelwert, **grau** die zum fremden Twin. **Die schwarze Linie** markiert die 0 (gleich gut). Die Zahlen im Kasten sind die Anteile der Personen, bei denen der Twin besser ist.

- **Fehler (links):** Nur bei **25 %** der Personen liegt der Twin näher als ihr Demografie-Mittelwert. Der Großteil der orangen Fläche liegt rechts der 0; typisch ist der Twin etwa 0,14 Punkte ungenauer.
- **Gegen den fremden Twin (links, grau):** Bei **74 %** ist der eigene Twin genauer. Der Twin enthält also für die meisten Personen Information über *diese* Person.
- **Individuelle Abweichung (rechts):** Hier ist es fast ein Gleichstand. Bei **51 %** der Personen trifft der Twin die individuelle Abweichung besser als der Demografie-Mittelwert, gegen den fremden Twin bei **74 %**.
- **Breite der Verteilungen:** Beide orangen Verteilungen sind breit. Es gibt also Personen, für die der Twin deutlich besser ist, und solche, für die er deutlich schlechter ist.

**Was die Abbildung aussagt:** Die Mittelwerte aus 1a und 1b verdecken keine Gruppe sehr guter Twins. Beim Abstand zur Antwort ist der Twin für die große Mehrheit schlechter als eine einfache demografische Schätzung. Bei der Rangfolge der Werte ist er für etwa jede zweite Person besser.

**Kernerkenntnis – Rangfolge ja, Niveau nein, für fast alle:** Das Ergebnis aus 1a und 1b gilt nicht nur im Mittel, sondern für die meisten einzelnen Twins. Wer einen Twin für eine bestimmte Person nutzt, bekommt mit hoher Wahrscheinlichkeit eine schlechtere Schätzung der Antworten als mit dem Demografie-Mittelwert, aber eine ähnlich gute Schätzung dessen, was der Person wichtiger ist als anderen.

**Einschränkung:** Ob einzelne Twins dauerhaft gut sind oder nur zufällig, lässt sich mit einem Lauf nicht trennen; dafür müsste derselbe Twin mehrfach erzeugt werden. Wie in 1a rechnet die Abbildung mit Erwartungswerten; mit gezogenen Antworten wären nur 7 % der Twins genauer als der Demografie-Mittelwert, und bei der individuellen Abweichung wären nur 41 % besser als er statt 51 %. Der Gleichstand rechts hängt also von der Wahl Erwartungswert/Ziehung ab (Sensitivitätsanalyse, DOKUMENTATION.md 5.6).

*N = 2 262 Personen, je Person ein Wert über 21 Fragen, Erwartungswerte der Twins. ρ: Spearman nach Abzug des Mittelwerts je Frage. Fremder Twin: Mittel über 20 Zufallspaarungen je Person.*
