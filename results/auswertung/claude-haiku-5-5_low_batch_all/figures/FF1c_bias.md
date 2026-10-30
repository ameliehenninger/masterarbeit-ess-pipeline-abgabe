# 1c – Liegt der Twin systematisch daneben?

Datei: `FF1c_bias.png`

Abbildung 1a hat gezeigt, *wie weit* der Twin im Mittel danebenliegt. Offen bleibt, *in welche Richtung*. Liegt der Twin mal zu hoch und mal zu tief, ist das Rauschen. Gibt er dagegen bei einer Frage fast allen Personen eine niedrigere Antwort, als sie selbst gegeben haben, ist das ein **systematischer Fehler (Bias)**: Das Modell hat dann eine eigene Vorstellung davon, wie wichtig dieser Wert ist, und überträgt sie auf alle.

Die Abbildung zeigt für jede der 21 Fragen, ob und in welche Richtung der Twin systematisch danebenliegt.

## Welche Maße verwendet werden und warum

**Mittlerer Fehler mit Vorzeichen (Mean Error, ME).** Für jede Person und jede Frage wird *Twin-Antwort minus Personen-Antwort* gerechnet, diesmal ohne den Betrag zu nehmen. Antwortet die Person mit 5 und der Twin mit 3, ergibt das −2; antwortet die Person mit 3 und der Twin mit 5, ergibt das +2. Diese Differenzen werden je Frage über alle 2 262 Personen gemittelt. Ein ME von −1 heißt: Der Twin antwortet bei dieser Frage im Schnitt einen ganzen Skalenpunkt niedriger als seine Person.

*Warum ME und nicht MAE wie in 1a?* Der MAE zählt jeden Fehler positiv. Er sagt, wie *groß* der Fehler ist, aber nicht, in welche Richtung er geht. Beim ME heben sich Fehler nach oben und nach unten gegenseitig auf. Bleibt trotzdem ein deutlicher Wert übrig, liegt der Twin überwiegend in eine Richtung daneben. Umgekehrt heißt ein ME nahe 0 *nicht*, dass der Twin genau ist: Bei „anderen helfen“ (Q12) ist der ME nur +0,03, der Twin liegt aber trotzdem im Mittel 0,67 Punkte neben seiner Person.

**Erwartungswerte.** Wie in 1a wird mit den Erwartungswerten des Twins gerechnet. Für die Richtung des Fehlers macht das kaum einen Unterschied, denn das Auslosen verschiebt den Mittelwert nicht: Gezogene Antworten haben in Erwartung denselben ME. Die Fehler streuen aber weniger, die Konfidenzintervalle werden etwas schmaler und Cohens d etwas größer. **ME und MAE ergänzen sich also: 1a misst die Größe des Fehlers, 1c seine Richtung.**

**95-%-Konfidenzintervall.** Der ME einer Frage beruht auf 2 262 Personen. Hätte man andere Personen befragt, käme ein etwas anderer Wert heraus. Das Konfidenzintervall gibt an, in welchem Bereich der „wahre“ ME vermutlich liegt, also der Wert, den man mit sehr vielen Personen erhalten würde. „95 %“ heißt: Würde man die Studie sehr oft mit neuen Stichproben wiederholen, würde das so berechnete Intervall in 95 von 100 Fällen den wahren Wert enthalten.

*Warum?* Es zeigt auf einen Blick, wie genau ein Wert bestimmt ist und ob er sich sicher von 0 unterscheidet.

**t-Test.** Er prüft je Frage: Wie wahrscheinlich wäre ein ME dieser Größe, wenn der Twin in Wahrheit gar keinen Bias hätte? Diese Wahrscheinlichkeit ist der **p-Wert**. Liegt er unter 5 % (α = 0,05), gilt der Bias als **signifikant**, also als nicht durch Zufall erklärbar.

**Holm-Korrektur.** Bei 21 Tests mit je 5 % Irrtumswahrscheinlichkeit würde man im Schnitt etwa einen Treffer finden, auch wenn es überall keinen Bias gäbe. Die Holm-Korrektur verschärft deshalb die Schwelle für jeden einzelnen Test so, dass das Risiko eines falschen Treffers über *alle* 21 Fragen zusammen bei 5 % bleibt.

**Mittlerer Fehler aller Fragen (gestrichelte Linie).** Der ME über alle 21 Fragen und alle Personen: −0,30. Er ist der allgemeine Versatz, um den der Twin insgesamt niedriger antwortet.

*Warum?* Über alle Fragen antwortet der Twin im Schnitt 0,30 Punkte niedriger als seine Person. Das kann ein **Antwortstil** sein: Das Modell kreuzt insgesamt zurückhaltender an, ohne einzelne Werte anders zu gewichten. Zieht man je Person den persönlichen Mittelwert über alle 21 Fragen ab (Zentrierung wie in Ebene 2), verschiebt sich jeder Balken um **genau** diesen Wert; das folgt direkt aus der Rechnung (Mittel der zentrierten Fehler = ME der Frage − ME aller Fragen). Die Zentrierung ändert also nicht die Reihenfolge, sondern nur den Nullpunkt. Deshalb zeigt die Abbildung keine zweite Balkenreihe, sondern nur die Linie: **Der Abstand eines Balkens zur Linie ist die Gewichtung dieses Werts im Verhältnis zu den übrigen.** Ebene 1 zeigt die Balken trotzdem ohne Zentrierung, weil die Frage dort lautet, wie weit die Antworten des Twins von den Antworten der Person entfernt sind; der Versatz gehört zu diesem Fehler dazu.

**Effektstärke Cohens d.** Bei 2 262 Personen werden auch sehr kleine Abweichungen signifikant. Cohens d gibt an, wie groß ein Bias im Verhältnis zur Streuung der Fehler ist (ME geteilt durch die Standardabweichung der Fehler). Werte um 0,2 gelten als klein, um 0,5 als mittel, um 0,8 als groß. Es steht nicht in der Abbildung (siehe `items.csv`).

## Was die Abbildung zeigt

**Die Balken** zeigen den ME je Frage. **Lila, nach links:** Der Twin hält den Wert für **unwichtiger** als die Person. **Braun, nach rechts:** Der Twin hält den Wert für **wichtiger**. Die Farben zeigen nur die Richtung und bedeuten nicht „gut“ oder „schlecht“.

**Die schwarzen Striche** sind die Konfidenzintervalle. Sie sind kurz (etwa ±0,05 Punkte), weil sehr viele Personen eingehen. Liegt ein Strich vollständig auf einer Seite der Null, ist die Richtung des Fehlers gesichert.

**Blasse Balken** haben den t-Test mit Holm-Korrektur nicht bestanden. Bei ihnen kreuzt auch das Konfidenzintervall die Null.

- **Bei 16 von 21 Fragen** liegt der Twin systematisch daneben, bei 14 davon nach unten.
- **Am stärksten unterschätzt** der Twin, wie wichtig der Person **Spaß haben** (−1,01), **erfolgreich sein** (−0,90), **kreativ sein** (−0,79), **starker Staat** (−0,76), **Abwechslung** und **Fähigkeiten zeigen** (je −0,73) sind. Beispiel Spaß haben: Die Personen antworten im Mittel mit 4,59, ihre Twins mit 3,58.
- **Überschätzt** werden nur zwei Fragen, beide zum Wert Konformität: **korrekt verhalten** (+0,68) und **Regeln befolgen** (+0,45).
- **Ohne gesicherten Bias** sind Gleichbehandlung, anderen helfen, sichere Umgebung, Umwelt schützen und Tradition. Das sind überwiegend Werte, die fast allen Menschen wichtig sind.
- Über alle Fragen zusammen liegt der ME bei **−0,30**: Der Twin antwortet im Schnitt etwas niedriger als seine Person.
- **Gegen die Linie gelesen:** Spaß haben (0,71 links der Linie), erfolgreich sein (0,60) und kreativ sein (0,49) gewichtet der Twin auch relativ zu seinen übrigen Antworten deutlich niedriger, korrekt verhalten (0,98 rechts) und Regeln befolgen (0,75) deutlich höher. Die Fragen, die bei 0 liegen (Tradition, Umwelt schützen, anderen helfen, Gleichbehandlung, sichere Umgebung), liegen rund 0,3 rechts der Linie: Relativ gewichtet der Twin sie etwas höher. Gegen die Linie getestet (t-Test auf den zentrierten Fehlern, Holm) weichen 20 von 21 Fragen signifikant ab, nur „reich sein“ liegt auf der Linie.

**Was die Abbildung aussagt:** Die Fehler des Twins sind nicht nur Rauschen, sondern folgen einem **klaren Muster**. Werte, die mit Vergnügen, Ehrgeiz und Neuem zu tun haben (Hedonismus, Leistung, Stimulation, Selbstbestimmung), stuft das Modell durchweg niedriger ein als die echten Menschen. Werte der Anpassung (Konformität) stuft es höher ein. Weil dieses Muster bei fast allen Twins auftritt, kommt es vom Modell selbst und nicht von den Profilen der einzelnen Personen.

**Kernerkenntnis – der „vernünftige, angepasste“ Twin:** Der Twin ähnelt eher einer vernünftigen, angepassten Durchschnittsperson als den tatsächlich Befragten. Ein Teil des Fehlers aus 1a lässt sich deshalb nicht durch bessere Angaben zur Person beheben, weil das Modell eine eigene Vorstellung davon mitbringt, was Menschen wichtig ist. Diese gerichteten Fehler erklären, warum der Twin beim MAE (1a) hinter dem Demografie-Mittelwert bleibt, obwohl er die individuelle Rangfolge der Person etwas besser trifft (1b). Das Muster taucht in 1d, 2a und 2c wieder auf.

**Antwortstil oder Gewichtung?** Beides. Ein Teil des Fehlers ist ein allgemeiner Versatz nach unten (−0,30), der Rest eine Umgewichtung, und die ist mit bis zu einem ganzen Skalenpunkt deutlich größer als der Versatz: Dem Twin sind Vergnügen, Erfolg und Kreativität weniger wichtig und Konformität wichtiger als der Person.

**Einschränkung – signifikant heißt nicht groß:** „Freunden loyal“ (−0,07) ist signifikant, inhaltlich aber kaum von Bedeutung (d = −0,10). Spaß haben (d = −0,80) und erfolgreich sein (d = −0,67) liegen dagegen im mittleren bis großen Bereich.

*N = 2 262 Personen, je 21 Fragen, Erwartungswerte der Twins. t-Test gegen 0 je Frage, Holm-korrigiert über 21 Fragen (α = 0,05); Konfidenzintervalle aus der t-Verteilung. Gestrichelte Linie: ME über alle Fragen; Test gegen die Linie = t-Test auf den je Person zentrierten Fehlern mit Holm-Korrektur (`items.csv`: `me_zentriert`, `p_zentriert_holm`).*
