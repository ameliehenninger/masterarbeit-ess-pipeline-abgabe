# A1 – Wie entsteht ein Twin?

Datei: `A1_beispielperson.png`

Für jede der 2 262 befragten Personen aus dem European Social Survey wurde ein „Twin“ erzeugt. Ein Sprachmodell erhält das Profil der Person, also Alter, Geschlecht, Bildung, Wohnort, Religion und weitere Angaben. Damit beantwortet es dieselben 21 Fragen zu persönlichen Werten, die auch die echte Person beantwortet hat.

Die Abbildung zeigt an **einer einzigen Person** (DE_50032), wie ein Twin entsteht und was die Größen bedeuten, die in allen folgenden Abbildungen vorkommen. Alle späteren Abbildungen fassen solche Paare aus Person und Twin zusammen.

## Welche Größen verwendet werden und warum

**Antwortskala.** Jede Frage beschreibt eine Person („Es ist ihr wichtig, kreativ zu sein …“). Die Befragten geben an, wie ähnlich sie dieser Person sind, von 1 („überhaupt nicht ähnlich“) bis 6 („sehr ähnlich“). Im Fragebogen bedeutet 1 „sehr ähnlich“; für die Auswertung ist die Skala **umgepolt**, damit ein hoher Wert durchgehend „wichtig“ heißt.

**Sechs Wahrscheinlichkeiten je Frage (Verbalized Sampling).** Das Modell nennt keine feste Antwort. Es gibt für jede der sechs Stufen an, wie wahrscheinlich sie ist, zum Beispiel „35 % für Stufe 5, 45 % für Stufe 6 …“.

*Warum?* Ein Sprachmodell, das nur seine wahrscheinlichste Antwort nennt, gibt ähnlichen Personen fast immer dieselbe Antwort. Die Wahrscheinlichkeiten sollen zeigen, wie sicher sich das Modell ist, und erlauben eine Ziehung.

**Gezogene Antwort.** Ein Programm lost aus den sechs Wahrscheinlichkeiten eine ganzzahlige Antwort aus, so wie man mit einem gezinkten Würfel würfelt. Diese Antwort steht in der synthetischen Stichprobe.

**Erwartungswert Σ k · pk.** Der Schwerpunkt der sechs Wahrscheinlichkeiten: jede Stufe k mal ihre Wahrscheinlichkeit pk, aufsummiert. Er ist die Antwort, die das Modell „im Durchschnitt“ meint, ohne den Zufall der Ziehung.

*Warum beide?* Ebene 1 (Twin gegen Person) rechnet mit dem Erwartungswert, weil es dort darum geht, was das Modell über die Person weiß. Ebene 2 (Population gegen Population) rechnet mit den gezogenen Antworten, weil dort die synthetische Stichprobe als Datensatz betrachtet wird.

**Fehler.** Der Abstand zwischen Twin-Antwort und Personen-Antwort in Skalenpunkten. Über alle 21 Fragen gemittelt ergibt sich der mittlere absolute Fehler (MAE) aus 1a.

## Was die Abbildung zeigt

**Links** stehen alle 21 Fragen der Person. **Blau** ist die echte Antwort der Person, **orange** die gezogene Antwort des Twins, der **orange Ring** der Erwartungswert. **Die graue Linie** verbindet Person und gezogene Antwort; ihre Länge ist der Fehler bei dieser Frage.

**Rechts** sind drei Fragen (A, B, C, links grau hinterlegt) aufgeschlüsselt. Die Balken sind die sechs Wahrscheinlichkeiten des Modells, der **kräftige Balken** die gezogene Antwort, die **gestrichelte Linie** der Erwartungswert, das **blaue Dreieck** die Antwort der Person. Die drei Fragen sind so gewählt, dass sie drei typische Fälle zeigen:

- **A „andere verstehen“ – Treffer:** Gezogen wird 5, die Person antwortet 5. Der Erwartungswert liegt mit 5,1 ebenfalls nah.
- **B „bescheiden sein“ – Pech bei der Ziehung:** Das Modell hält 4 für am wahrscheinlichsten (Erwartungswert 3,7), gezogen wird aber 2 mit nur 13 % Wahrscheinlichkeit. Die Person antwortet 4. Der Erwartungswert hätte fast getroffen, die Ziehung liegt 2 Punkte daneben.
- **C „korrekt verhalten“ – das Modell liegt schon im Mittel daneben:** Das Modell erwartet 4,9, die Person antwortet 2. Hier hilft auch der Erwartungswert nicht; das ist der systematische Fehler aus 1c (Konformität überschätzt).

**Was die Abbildung aussagt:** Bei dieser Person liegt der Twin mit gezogenen Antworten im Mittel **1,00 Skalenpunkte** daneben, mit Erwartungswerten **0,86**. Der Unterschied entsteht allein durch den Zufall der Ziehung (Fall B). Ein Teil des Fehlers bleibt aber auch ohne Ziehung, weil das Modell eine eigene Vorstellung davon hat, wie wichtig manche Werte sind (Fall C).

**Kernerkenntnis – zwei Fehlerquellen:** Der Fehler eines Twins hat zwei Ursachen, die sich in allen späteren Abbildungen wiederfinden: das **Rauschen der Ziehung**, das per Konstruktion nichts über die Person verrät (siehe A2), und die **gerichteten Fehler des Modells** (siehe 1c).

**Einschränkung:** Eine einzelne Person ist ein Beispiel, kein Beleg. Die Person wurde zur Veranschaulichung gewählt; ihr Fehler (1,00 gezogen) liegt etwas unter dem Durchschnitt aller Twins (1,34).

*Person DE_50032 (ESS 11, Deutschland) und ihr Twin, 21 Fragen. Rechts drei Beispielfragen; Wahrscheinlichkeiten aus `antworten_LLM_detail.csv`.*
