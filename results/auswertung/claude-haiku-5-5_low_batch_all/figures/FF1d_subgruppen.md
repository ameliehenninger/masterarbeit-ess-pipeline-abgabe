# 1d – Trifft der Twin manche Gruppen schlechter?

Datei: `FF1d_subgruppen.png`

Abbildung 1a hat gezeigt, dass der Twin im Mittel **1,06 Skalenpunkte** neben seiner Person liegt (Erwartungswerte, siehe 1a). Dieser Wert ist ein Durchschnitt über alle 2 262 Personen. Er kann verdecken, dass das Modell manche Menschen gut und andere schlecht trifft.

Die Abbildung teilt die Personen deshalb nach sieben Merkmalen in Gruppen auf: Geschlecht, Alter, Schulabschluss, Wohnort, Region (Ost/West), Religionszugehörigkeit und Werte-Milieu (siehe 2.1). Sie zeigt, ob der Twin bei manchen Gruppen weiter danebenliegt als bei anderen.

## Welche Maße verwendet werden und warum

**MAE je Gruppe.** Für jede Gruppe wird der mittlere absolute Fehler aus 1a getrennt berechnet. Dargestellt ist die Abweichung vom Gesamtfehler: *MAE der Gruppe minus 1,06*.

*Warum die Abweichung?* So ist sofort zu sehen, ob eine Gruppe besser oder schlechter getroffen wird als der Durchschnitt.

**Einfaktorielle Varianzanalyse (ANOVA).** Bei 1c wurde mit dem t-Test geprüft, ob *ein* Mittelwert von 0 abweicht. Hier geht es um eine andere Frage: Unterscheiden sich die MAE-Werte *mehrerer Gruppen* voneinander, etwa der fünf Altersgruppen? Dafür ist die ANOVA das übliche Verfahren. Sie prüft je Merkmal, ob die Gruppenunterschiede größer sind, als der Zufall erwarten lässt.

**Holm-Korrektur.** Weil sieben Merkmale getestet werden, wird wie in 1c korrigiert: Die Schwelle wird so verschärft, dass das Risiko eines Zufallstreffers über alle sieben Tests zusammen bei 5 % bleibt.

**Kruskal-Wallis-Test als Kontrolle.** Die ANOVA setzt voraus, dass die Fehler ungefähr normalverteilt sind. Der Kruskal-Wallis-Test braucht diese Annahme nicht, weil er nur mit Rangplätzen rechnet (wie der Wilcoxon-Test in 1a). Kommen beide Tests zum selben Ergebnis, ist der Befund robust.

**Effektstärke η² (Eta-Quadrat).** Wie Cohens d in 1c beantwortet η² die Frage, wie *groß* ein Unterschied ist, nicht nur ob er gesichert ist. η² gibt an, welcher Anteil der Fehlerunterschiede zwischen den Twins durch das Merkmal erklärt wird. η² = 0,039 heißt: 3,9 % der Unterschiede im MAE gehen auf den Schulabschluss zurück, 96,1 % haben andere Gründe. Werte um 0,01 gelten als klein, um 0,06 als mittel, um 0,14 als groß.

**Multiple Regression.** Die Merkmale hängen zusammen; Menschen in Ostdeutschland sind zum Beispiel seltener religiös gebunden. Die ANOVA betrachtet jedes Merkmal einzeln und kann solche Überschneidungen nicht trennen. Eine Regression nimmt die sechs demografischen Merkmale gleichzeitig auf und zeigt, welches Merkmal *für sich* einen Einfluss hat. **R²** gibt an, welcher Anteil der Fehlerunterschiede durch alle Merkmale zusammen erklärt wird.

## Was die Abbildung zeigt

**Pinke Balken, nach rechts:** Der Twin liegt bei dieser Gruppe **weiter daneben** als im Schnitt. **Grüne Balken, nach links:** Der Twin trifft diese Gruppe **besser**. **Blasse Balken:** Das Merkmal hat den Test nicht bestanden. **Die Zahl neben dem Balken** ist der MAE der Gruppe selbst, **n** in Klammern die Zahl der Personen.

**Wichtig: Die Achse reicht nur von −0,1 bis +0,1 Skalenpunkten.** Die Balken wirken dadurch groß, die Unterschiede sind aber klein. Der größte Unterschied (niedrige Bildung, +0,09) entspricht etwa 8 % des Fehlers.

| Merkmal | η² | p (ANOVA, Holm) | signifikant |
|---|---|---|---|
| Werte-Milieu | 0,040 | < 0,001 | ja |
| Schulabschluss | 0,039 | < 0,001 | ja |
| Religion | 0,007 | < 0,001 | ja |
| Alter | 0,007 | 0,009 | ja |
| Region | 0,007 | < 0,001 | ja |
| Wohnort | 0,001 | 0,46 | nein |
| Geschlecht | 0,000 | 0,92 | nein |

- **Schulabschluss:** Bei niedriger Bildung liegt der Twin am weitesten daneben (1,15), bei hoher Bildung am wenigsten (1,01).
- **Religion:** Bei religiös gebundenen Personen ist der Twin etwas genauer (1,04) als bei nicht gebundenen (1,09).
- **Region:** In Ostdeutschland ist der Twin etwas ungenauer (1,11) als im Westen (1,05).
- **Alter:** Der Fehler steigt leicht mit dem Alter, von 1,03 bis 1,05 bei den Jüngeren auf 1,11 bei den über 75-Jährigen.
- **Werte-Milieu:** Personen aus Milieu 1 (offen) trifft der Twin schlechter (1,11) als Personen aus Milieu 2 (bewahrend, 1,00). Das ist zusammen mit dem Schulabschluss der größte Effekt.
- **Geschlecht und Wohnort** machen keinen gesicherten Unterschied.
- **Regression:** Alle sechs demografischen Merkmale zusammen erklären nur **R² = 5,7 %** der Fehlerunterschiede. Signifikant bleiben der Schulabschluss (mittel −0,09, hoch −0,13 Punkte gegenüber niedrig), die Religion (nicht gebunden +0,05) und die Region (Ost +0,05). Das Alter ist neben den anderen Merkmalen nicht mehr signifikant.

**Was die Abbildung aussagt:** Der Twin ist **für alle Gruppen ähnlich ungenau**. Es gibt keine Gruppe, für die er gut funktioniert, und keine, für die er völlig versagt. Die gefundenen Unterschiede sind statistisch gesichert, aber klein. Auffällig ist der Bildungsbefund: Das Modell scheint Personen mit hoher Bildung besser einschätzen zu können als Personen mit niedriger Bildung.

**Kernerkenntnis – offene Menschen werden schlechter getroffen:** Den größten Effekt hat das Werte-Milieu, also kein demografisches Merkmal, sondern das, was der Person wichtig ist. Abbildung 1c hat gezeigt, dass das Modell Spaß, Erfolg, Kreativität und Abwechslung systematisch unterschätzt und Konformität überschätzt. Genau diese offenen Werte prägen Milieu 1. Personen, die von der „vernünftigen, angepassten“ Vorstellung des Modells abweichen, trifft der Twin deshalb schlechter.

**Einschränkung – das Werte-Milieu ist kein äußeres Merkmal (Stern in der Abbildung):** Anders als Alter oder Bildung wird das Milieu aus den Antworten der Person selbst gebildet (2.1). Der Effekt ist deshalb kein unabhängiger Gruppenbefund, sondern zum Teil konstruktionsbedingt: Wer im offenen Milieu landet, hat genau die Werte hoch angegeben, die das Modell systematisch unterschätzt (1c). Der Befund zeigt also, *wen* der Bias aus 1c trifft, nicht eine zusätzliche Fehlerquelle. In die Regression geht das Milieu deshalb nicht ein.

**Erwartungswerte:** Wie in 1a beruhen die Werte auf den Erwartungswerten des Twins. Mit gezogenen Antworten käme allen Gruppen gleichermaßen Zufall hinzu, der die Unterschiede eher verkleinert.

*N = 2 262 Personen (je Merkmal ohne fehlende Angaben), Erwartungswerte der Twins. Einfaktorielle ANOVA je Merkmal, Holm-korrigiert über 7 Merkmale (α = 0,05); Kontrolle mit Kruskal-Wallis; Regression: n = 2 243, R² = 0,057.*
