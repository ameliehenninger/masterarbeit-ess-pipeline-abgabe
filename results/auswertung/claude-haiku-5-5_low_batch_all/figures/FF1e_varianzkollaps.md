# 1e – Werden die Twins einer Demografie-Gruppe zu ähnlich?

Datei: `FF1e_varianzkollaps.png`

Sprachmodelle neigen zum **Varianzkollaps**: Sie geben Personen mit ähnlichem Profil sehr ähnliche Antworten, nämlich die, die das Modell für „typisch“ hält. Echte Menschen sind vielfältiger. Zwei 40-jährige Frauen mit Abitur können völlig unterschiedliche Werte haben.

Die Abbildung zeigt, ob die Twins diese Vielfalt nachbilden oder ob sie innerhalb einer Gruppe gleicher Demografie zu einheitlich antworten.

## Welche Maße verwendet werden und warum

**Demografie-Zellen.** Die Personen werden nach Geschlecht, Altersgruppe und Bildung in Zellen eingeteilt, zum Beispiel „Frauen, 30–44 Jahre, hohe Bildung“. Berücksichtigt werden nur die 30 Zellen mit mindestens 20 Personen (2 250 Personen).

*Warum Zellen?* Innerhalb einer Zelle sind sich die Personen in diesen drei Merkmalen gleich. Jede Streuung, die dort noch bleibt, ist **individuelle Vielfalt**. Genau die geht beim Varianzkollaps verloren.

**Standardabweichung (SD).** Die SD gibt an, wie weit die Antworten im Mittel um ihren Durchschnitt streuen, in Skalenpunkten. SD = 0 heißt, alle haben dasselbe geantwortet; SD = 1,2 heißt, die Antworten liegen im Mittel gut einen Punkt vom Durchschnitt entfernt. Die SD wird je Frage und je Zelle berechnet und dann über die Zellen gemittelt, gewichtet nach Zellgröße.

*Warum die SD?* Sie hat dieselbe Einheit wie die Antworten und ist deshalb direkt mit dem MAE aus 1a vergleichbar.

**95-%-Band der Personen (Bootstrap).** Es zeigt, wie stark die Streuung der Personen allein durch den Zufall der Stichprobe schwanken würde. Dafür werden die Personen jeder Zelle 1 000-mal neu zufällig gezogen, und jedes Mal wird die SD berechnet. Das Band umfasst die mittleren 95 % dieser Werte.

*Warum Bootstrap?* Das Band erfüllt dieselbe Aufgabe wie das Konfidenzintervall in 1c. Für eine über Zellen gemittelte SD gibt es aber keine einfache Formel, deshalb wird es durch Neuziehen gewonnen.

**Gezogene Antworten und Erwartungswerte.** Wie in 1a wird die Streuung der Twins zweimal berechnet: mit den **gezogenen Antworten**, die aus den sechs Wahrscheinlichkeiten des Modells ausgelost wurden, und mit den **Erwartungswerten**, also der Antwort, die das Modell „im Durchschnitt“ meint.

*Warum beides?* So lässt sich trennen, wie viel Vielfalt vom Modell selbst kommt und wie viel erst durch das Auslosen entsteht.

## Was die Abbildung zeigt

**Der blaue Punkt** zeigt die Streuung der echten Personen, **das hellblaue Band** ihren Zufallsbereich. **Der gefüllte orange Punkt** zeigt die Streuung der gezogenen Twin-Antworten, **der orange Ring** die der Erwartungswerte. **Die graue Linie** verbindet Personen und gezogene Antworten. **Weiter rechts bedeutet: mehr Vielfalt.** Liegt ein Twin-Punkt außerhalb des Bandes, streuen die Twins gesichert anders als die Personen.

**Die gefüllten Punkte** liegen bei **17 von 21 Fragen rechts vom Band**: Die gezogenen Antworten streuen stärker als die Personen, im Mittel mit SD **1,27** gegenüber **1,13**. Nur bei drei Fragen (Abwechslung, korrekt verhalten, Fähigkeiten zeigen) streuen sie weniger. Bei Abwechslung ist das in A2 umgekehrt (dort streuen die Twins stärker). Der Grund ist das Maß: 1e misst die Streuung *innerhalb* gleicher Demografie, A2 über *alle* Personen; bei Abwechslung unterscheiden die Twins vor allem zwischen den Demografie-Gruppen, kaum innerhalb.

**Sortierung:** Die Fragen sind nach dem Abstand gezogene Twins − Personen sortiert; oben streuen die Twins am stärksten mehr als die Personen.

**Die Ringe** liegen bei **allen 21 Fragen weit links vom Band**, im Mittel bei SD **0,53**, also weniger als halb so viel wie bei den Personen. Bei „Freunden loyal“ (0,16) oder „frei entscheiden“ (0,27) unterscheiden sich die Twins einer Zelle in ihrer eigentlichen Einschätzung kaum.

**Was die Abbildung aussagt:** Auf den ersten Blick gibt es keinen Kollaps, auf den zweiten doch. Das Modell selbst unterscheidet Personen gleicher Demografie **kaum voneinander**; seine Einschätzungen, die Erwartungswerte, sind stark kollabiert. Dass die gezogenen Antworten trotzdem breit streuen, liegt am **Auslosen**: Jeder Twin bekommt eine eher unsichere Verteilung über die sechs Stufen, zum Beispiel „30 % Stufe 4, 25 % Stufe 3, 20 % Stufe 5 …“. Das Auslosen erzeugt daraus unterschiedliche Antworten, auch wenn die Verteilungen zweier Twins fast gleich sind. Diese Vielfalt ist **Zufall und keine Information über die Person**.

**Kernerkenntnis – geliehene Vielfalt:** Das erklärt den Zielkonflikt aus 1a. Die Ziehung lässt die simulierte Population vielfältig *aussehen*, kostet aber Genauigkeit bei der einzelnen Person (MAE 1,34 statt 1,06). Wie groß der Anteil des Zufalls ist, zeigt Abbildung A2: Nur rund **30 %** der Streuung der gezogenen Antworten unterscheiden die Twins tatsächlich voneinander, etwa 70 % entstehen erst durch das Auslosen.

**Einschränkung:** Erwartungswerte sind Mittelwerte einer Verteilung und liegen schon rechnerisch näher an der Skalenmitte als einzelne Antworten. Ein Teil ihrer geringen Streuung ist deshalb mechanisch bedingt. Bei einer Halbierung der SD ist der Abstand aber zu groß, um nur daran zu liegen. Auch die Varianzzerlegung in A2 zeigt die geringe Streuung zwischen den Twins, und dort tritt dieses Problem nicht auf.

*N = 2 250 Personen in 30 Demografie-Zellen (Geschlecht × Altersgruppe × Bildung, je ≥ 20 Personen). SD je Zelle, gewichtet gemittelt. Band: 1 000 Bootstrap-Stichproben der Personen je Zelle, 2,5- bis 97,5-%-Quantil.*
