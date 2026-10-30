# 1a – Wie weit liegt der Twin bei seiner Person daneben?

Datei: `FF1a_genauigkeit.png`

Für jede der 2 262 befragten Personen aus dem European Social Survey wurde ein „Twin“ erzeugt. Ein Sprachmodell erhält das Profil der Person, also Alter, Geschlecht, Bildung, Wohnort, Religion und weitere Angaben. Damit beantwortet es dieselben 21 Fragen zu persönlichen Werten, die auch die echte Person beantwortet hat. Jede Frage hat sechs Antwortstufen, von 1 („überhaupt nicht ähnlich“) bis 6 („sehr ähnlich“).

Die Abbildung zeigt, wie weit die Antworten des Twins im Mittel von den echten Antworten seiner Person entfernt sind.

## Welche Maße verwendet werden und warum

**Erwartungswert als Antwort des Twins.** Das Modell nennt keine feste Antwort, sondern sechs Wahrscheinlichkeiten, zum Beispiel „30 % für Stufe 4, 20 % für Stufe 3 …“ (Verbalized Sampling). Der **Erwartungswert** ist der Schwerpunkt dieser Wahrscheinlichkeiten, also die Antwort, die das Modell „im Durchschnitt“ meint. Für die synthetische Stichprobe lost ein Programm daraus zusätzlich eine ganzzahlige Antwort aus (**gezogene Antwort**), so wie man mit einem gezinkten Würfel würfelt.

*Warum hier der Erwartungswert?* Ebene 1 fragt, was das Modell über die Person weiß. Die Ziehung fügt Zufall hinzu, der per Konstruktion nichts über die Person verrät. Außerdem sind die Vergleichsgrößen (Mittelwert, Demografie-Mittelwert) selbst Durchschnitte ohne Ziehung. Würde man sie mit der gezogenen Antwort vergleichen, trüge nur der Twin dieses Rauschen. Mit Erwartungswerten werden Durchschnitte mit Durchschnitten verglichen. Ebene 2, die die simulierte Population als Datensatz betrachtet, rechnet dagegen mit den gezogenen Antworten.

**Mittlerer absoluter Fehler (MAE).** Je Frage wird der Abstand zwischen Twin-Antwort und Personen-Antwort in Skalenpunkten gemessen, und zwar ohne Vorzeichen. Dann wird über alle 21 Fragen und alle Personen gemittelt. Antwortet die Person mit 4 und meint der Twin 2,5, beträgt der Fehler bei dieser Frage 1,5 Punkte. **Ein kürzerer Balken bedeutet also eine genauere Vorhersage.**

*Warum der MAE?* Er ist das anschaulichste Maß für Genauigkeit, weil er dieselbe Einheit hat wie die Antworten: „MAE 1,06“ heißt direkt „im Mittel 1,06 Skalenpunkte daneben“. Weil das Vorzeichen wegfällt, können sich Fehler nach oben und nach unten nicht gegenseitig aufheben. Die Richtung der Fehler wird erst in 1c mit dem Mean Error untersucht. Ergänzend wurde der **RMSE** (Wurzel aus dem mittleren quadrierten Fehler) berechnet. Er gewichtet große Fehler stärker. Beim Twin liegt er bei 1,34, beim fremden Twin bei 1,46 und beim Mittelwert aller Personen bei 1,15. Die Reihenfolge ist dieselbe wie beim MAE; die Abbildung zeigt deshalb nur den MAE.

**Vergleichsgrößen (graue Balken).** Ein MAE von 1,06 sagt allein nicht, ob das gut oder schlecht ist. Vor allem sagt er nicht, *woher* die Nähe kommt: Kennt das Modell die Person, oder weiß es nur, wie Menschen in Deutschland typischerweise antworten? Deshalb wird der Twin mit Vorhersagen verglichen, die **nichts über die einzelne Person wissen** (siehe unten). Schlägt der Twin diese nicht, nützt ihm das Profil der Person nichts.

**Oranger Punkt: gezogene Antworten.** Er zeigt denselben Fehler mit den ausgelosten Antworten, also das, was in der synthetischen Stichprobe tatsächlich steht. Die Differenz zum Balken ist allein der Preis der Ziehung.

**Wilcoxon-Test.** Er prüft, ob der Twin wirklich besser ist als der fremde Twin oder ob der Unterschied (1,06 gegenüber 1,18) Zufall sein könnte. Dafür wird für **jede Person einzeln** verglichen, ob ihr eigener Twin oder der fremde Twin näher lag. Der Test prüft dann, ob der eigene Twin über alle Personen hinweg häufiger und deutlicher vorne liegt, als es bei reinem Zufall zu erwarten wäre. Gewählt wurde der Wilcoxon-Test statt eines t-Tests (siehe 1c), weil er nur mit Rangplätzen rechnet und keine Normalverteilung der Fehler voraussetzt. Ergebnis: **p < 0,001**, der Vorsprung ist gesichert. Bei **74 %** der Personen liegt der eigene Twin näher als der fremde.

## Was die Abbildung zeigt

**Der orange Balken** zeigt den Twin: Er liegt im Mittel **1,06 Skalenpunkte** daneben.

**Der orange Punkt (1,34)** zeigt denselben Twin mit gezogenen Antworten.

**Die grauen Balken** sind Vergleichsgrößen, die **nichts über die einzelne Person wissen**:

- **Fremder Twin (1,18):** die Antworten eines Twins, der für eine *andere* Person erzeugt wurde, ebenfalls als Erwartungswerte. Er teilt mit dem eigenen Twin Modell, Anweisung und systematische Fehler. Der Unterschied zwischen beiden ist also genau das, was das Profil der Person beiträgt.
- **Mittelwert aller Personen (0,95):** Für jede Frage wird einfach die Durchschnittsantwort aller Befragten eingesetzt.
- **Demografie-Mittelwert (0,92):** die Durchschnittsantwort der *anderen* Personen mit gleichem Geschlecht, gleicher Altersgruppe und gleichem Bildungsabschluss. Er weiß nichts über die Person, kennt aber die echten Antworten aller anderen Befragten, die dem Modell fehlen. Er ist damit die Messlatte, die eine Forscherin mit ESS-Daten auch ohne Sprachmodell erreicht.

Würfeln (jede Antwort von 1 bis 6 gleich wahrscheinlich) ergäbe 1,88. Das schlägt jedes sinnvolle Verfahren und ist deshalb nicht mehr in der Abbildung.

**Was die Abbildung aussagt:** Der Twin ist besser als der Twin einer fremden Person. Er enthält also Information über seine Person. Er ist aber **ungenauer als einfache Durchschnittswerte**, die die Person gar nicht kennen: 1,06 gegenüber 0,95 (Mittelwert) und 0,92 (Demografie-Mittelwert). Das liegt nicht an der Ziehung, denn hier werden Durchschnitte mit Durchschnitten verglichen. Es liegt an den gerichteten Fehlern des Modells (siehe 1c). Wer die Antworten einer Person vorhersagen will, liegt mit dem Durchschnitt der Bevölkerung im Mittel näher als mit ihrem Twin. Nur **25 %** der Twins sind genauer als ihr Demografie-Mittelwert (siehe A3).

**Kernerkenntnis – der Preis der Ziehung:** Die Ziehung aus den verbalisierten Wahrscheinlichkeiten hat zwei Seiten. Sie vergrößert die Streuung der Twin-Antworten und lässt die Population breit genug wirken (siehe 2b und A2). Dafür erhöht sie den mittleren Fehler merklich, von **1,06 auf 1,34**, also um gut ein Viertel. Mehr Vielfalt in der Population wird hier mit weniger Genauigkeit bei der einzelnen Person bezahlt, und diese Vielfalt ist Zufall, keine Information.

**Robustheit der Ziehung:** Die gezogenen Antworten stammen aus einer einzigen Ziehung. Zieht man aus denselben Wahrscheinlichkeiten 20-mal neu, liegt der MAE stets zwischen **1,34 und 1,36**. Der orange Punkt hängt also nicht vom Zufall dieser einen Ziehung ab.

**Einschränkung:** Erwartungswert und gezogene Antwort stammen aus *derselben* Wahrscheinlichkeitsverteilung. Der Vergleich zeigt also, was die Ziehung kostet, nicht wie ein Lauf ganz ohne Verbalized Sampling abgeschnitten hätte; dieser Vergleichslauf fehlt. Ebenso beruht alles auf einem einzigen Modellaufruf je Person; wie stark die Wahrscheinlichkeiten selbst bei einem erneuten Aufruf schwanken würden, ist nicht geprüft.

*N = 2 262 Personen, je 21 Fragen, Erwartungswerte der Twins (Punkt: gezogene Antworten). Unterschied Twin gegenüber fremdem Twin: Wilcoxon-Test, p < 0,001.*
