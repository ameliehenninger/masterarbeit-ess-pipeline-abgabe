# A2 – Woher kommt die Breite der Twins?

Datei: `A2_varianzzerlegung.png`

Eine synthetische Stichprobe ist nur brauchbar, wenn sie so vielfältig ist wie die echte Bevölkerung. Sprachmodelle neigen aber zum **Varianzkollaps**: Sie geben ähnlichen Personen sehr ähnliche Antworten. Die Ziehung aus sechs Wahrscheinlichkeiten (siehe A1) soll dem entgegenwirken.

Die Abbildung zeigt, woher die Vielfalt der Twins kommt: aus echten Unterschieden zwischen den Twins oder aus dem Zufall der Ziehung.

## Welche Maße verwendet werden und warum

**Varianz.** Die Varianz einer Frage misst, wie stark die Antworten zwischen den Personen schwanken. Sie ist das Quadrat der Standardabweichung, ihre Einheit ist deshalb Skalenpunkte².

**Satz von der totalen Varianz.** Die Varianz der gezogenen Twin-Antworten lässt sich exakt in zwei Teile zerlegen:

- **zwischen den Twins:** wie stark sich die Erwartungswerte der Twins voneinander unterscheiden. Das ist die Vielfalt, die das Modell selbst erzeugt, also echte Information über unterschiedliche Personen.
- **durch die Ziehung:** wie stark die gezogene Antwort im Mittel um den Erwartungswert desselben Twins schwankt, also die Varianz innerhalb jedes Twins (seines Wahrscheinlichkeitsvektors). Das ist reiner Zufall; zieht man für denselben Twin neu, käme eine andere Antwort heraus.

*Warum?* Nur so lässt sich trennen, ob die Twins vielfältig sind, weil das Modell die Personen unterscheidet, oder nur, weil gewürfelt wird. Die Zerlegung braucht keine Annahme über die Verteilung und kommt ohne Zellbildung aus (anders als 1e).

**Anteil zwischen den Twins.** Der erste Teil geteilt durch die gesamte Varianz der Twins.

## Was die Abbildung zeigt

**Jede Zeile** ist eine Frage, sortiert nach der Gesamtvarianz der Twins. **Der kräftige Teil** des Balkens ist die Varianz zwischen den Twins, **der blasse Teil** die Varianz durch die Ziehung; zusammen ergeben sie die Varianz der gezogenen Antworten. **Der blaue Punkt** ist die Varianz der echten Personen. **Die Zahl in der rechten Spalte** ist der Anteil zwischen den Twins.

- **Nur rund 30 %** der Streuung der Twins unterscheidet die Twins voneinander, rund 70 % entstehen durch die Ziehung.
- **Insgesamt** sind die Twins sogar etwas breiter als die Personen (Summe über die 21 Fragen × 1,33). Die Unterschiede *zwischen* den Twins erreichen aber nur rund 40 % der Varianz der Personen.
- **Am höchsten** ist der Anteil bei Tradition (53 %) und Regeln befolgen (49 %). Hier unterscheidet das Modell die Personen am deutlichsten, wohl weil Religion und Alter im Profil stehen (siehe 1b′ und Fazit 3).
- **Am niedrigsten** ist er bei Freunden loyal (4 %), frei entscheiden (8 %) und anderen helfen (13 %). Hier gibt das Modell fast allen Twins dieselbe Verteilung; jede Vielfalt stammt aus der Ziehung.
- **Eine Ausnahme vom Kollaps:** Bei „andere verstehen“ unterscheiden sich die Twins schon in ihren Erwartungswerten stärker als die Personen (Varianz 0,81 gegen 0,75). Bei allen anderen 20 Fragen liegt die Varianz zwischen den Twins unter der der Personen.
- **Bei zwei Fragen** (Fähigkeiten zeigen, korrekt verhalten) erreichen die Twins nicht einmal mit Ziehung die Breite der Personen.

**Was die Abbildung aussagt:** Die simulierte Population **wirkt vielfältig, aber die Vielfalt ist überwiegend Zufall**. Das Modell selbst unterscheidet die Personen deutlich weniger, als sich echte Menschen unterscheiden.

**Kernerkenntnis – geliehene Vielfalt:** Die Ziehung löst das Problem des Varianzkollapses nur scheinbar. Sie erzeugt Breite, aber keine Information über die Person. Deshalb kostet sie auf Ebene 1 Genauigkeit (MAE 1,34 statt 1,06, siehe 1a), und deshalb liegt der Twin auch mit Ziehung kaum öfter im Milieu seiner Person (2d).

**Einschränkung:** Auch die Antwort einer echten Person ist eine einzelne Antwort mit Messfehler; ihre Varianz enthält also ebenfalls einen Zufallsanteil. Der Vergleich der Erwartungswerte (kräftig) mit den Personen (Punkt) überzeichnet den Kollaps deshalb etwas. Der Vergleich der ganzen Balken mit dem Punkt ist dagegen fair (Antwort gegen Antwort). Der Faktor 1,33 weicht vom Faktor 1,39 in 2b ab, weil 2b über die 10 zentrierten Werte summiert statt über die 21 Fragen.

*N = 2 262 Personen, 21 Fragen. Varianz der Erwartungswerte Σ k · pk zwischen den Twins plus mittlere Varianz innerhalb jedes Wahrscheinlichkeitsvektors (Satz von der totalen Varianz).*
