# 2b – Ist die simulierte Population gleich breit?

Datei: `FF2b_streuung.png`

Abbildung 2a hat gefragt, *wo* die Milieus liegen. Zwei Populationen können aber am selben Ort liegen und trotzdem verschieden sein: Die eine kann eng beieinander liegen, die andere weit gestreut.

Die Abbildung zeigt, wie **breit** die simulierte Population im Vergleich zur echten ist. Damit wird der Varianzkollaps aus 1e noch einmal geprüft, diesmal für die ganze Population und über alle 10 Werte gleichzeitig.

## Welche Maße verwendet werden und warum

**Gesamtstreuung tr(Σ).** Die **Varianz** eines Werts misst, wie stark er zwischen den Menschen schwankt; sie ist das Quadrat der Standardabweichung aus 1e. Für jeden der 10 zentrierten Werte wird die Varianz berechnet, und die 10 Varianzen werden addiert. (Mathematisch ist das die Spur der Kovarianzmatrix, daher die Abkürzung tr(Σ).) Zur Orientierung: 7,2 entspricht einer Standardabweichung von etwa 0,85 Skalenpunkten je Wert, 10,0 etwa 1,0.

*Warum?* Die Gesamtstreuung fasst die **Breite der ganzen Wertewolke** in einer Zahl zusammen. Aussagekräftig ist sie vor allem im Verhältnis Twins zu Personen.

**Bures-Wasserstein-Distanz (nur im Text, nicht in der Abbildung).** Die **Kovarianzmatrix** ist eine Tabelle, die für jedes Wertepaar angibt, wie stark die beiden zusammen schwanken, etwa ob Personen, denen Hedonismus wichtig ist, auch Stimulation wichtig finden. Die Bures-Wasserstein-Distanz vergleicht die Kovarianzmatrizen von Personen und Twins als Ganzes. **0 heißt: gleich breit, gleich ausgerichtet, gleiche Zusammenhänge.** Je größer der Wert, desto unterschiedlicher die Form.

*Warum zusätzlich?* tr(Σ) sagt nur, *wie breit* eine Wolke ist, nicht *in welche Richtung* sie sich ausdehnt. Zwei Wolken können gleich breit sein, die eine aber länglich in Richtung Offenheit, die andere in Richtung Selbsttranszendenz. Die Bures-Wasserstein-Distanz erkennt das.

**Rauschen.** Wie in 2a werden die Personen in zwei Zufallshälften geteilt, und es wird die Bures-Wasserstein-Distanz zwischen den Hälften berechnet. Dieser Wert zeigt, wie groß die Distanz allein durch Zufall wäre.

**Gezogene Antworten und Erwartungswerte.** Wie in 1a und 1e wird die Streuung der Twins zweimal berechnet: mit den gezogenen Antworten und mit den Erwartungswerten, also ohne den Zufall des Auslosens.

## Was die Abbildung zeigt

**Für die Gesamtpopulation und jedes Milieu** gibt es drei Balken (je Milieu gilt für beide Twin-Balken dieselbe Einteilung, die aus den gezogenen Antworten in 2.1): **blau** die Personen, **kräftiges Orange** die Twins mit gezogenen Antworten, **helles Orange** die Twins mit Erwartungswerten. In Klammern steht das Verhältnis zu den Personen (Faktor).

- **Gezogene Antworten: breiter.** Insgesamt streuen die Twins **× 1,39** so stark wie die Personen (10,0 statt 7,2). Innerhalb der Milieus sind es × 1,25 bzw. × 1,26.
- **Erwartungswerte: deutlich enger.** Ohne den Zufall des Auslosens erreichen die Twins nur **× 0,61** der Streuung der Personen (4,4 statt 7,2), innerhalb der Milieus × 0,48 bzw. × 0,39.
- **Die Form unterscheidet sich.** Die Bures-Wasserstein-Distanz beträgt insgesamt **0,77**, das **4,5-Fache des Rauschens** (0,17). Auch je Milieu liegt sie mit 0,52 und 0,60 klar über dem Rauschen (0,21 und 0,22). Weil die Arbeit nicht nach den Zusammenhängen zwischen den Werten fragt, steht dieser Wert nur hier und nicht in der Abbildung.
- **Unabhängig von der Ziehung:** Zieht man aus denselben Wahrscheinlichkeiten 20-mal neu, liegt der Faktor stets zwischen × 1,39 und × 1,42.
- **Anderer Faktor als in A2:** A2 vergleicht die Varianz der 21 einzelnen Fragen (Twins × 1,33), 2b die Summe über die 10 zentrierten Werte (× 1,39). Beides zeigt dieselbe Richtung.
- **Vorsicht beim Vergleich je Milieu:** Die Twin-Milieus sind anders geschnitten (39 statt 55 % im offenen Milieu). Ein Teil der Unterschiede je Milieu kommt deshalb schon von der Einteilung; der Gesamtvergleich ist davon frei.
- **Gesamt breiter als die Milieus:** Die Gesamtstreuung ist überall größer als die Streuung innerhalb der Milieus, weil der Abstand *zwischen* den Milieus hinzukommt. Bei den Twins ist dieser Zuwachs besonders groß: von 7,6 bzw. 7,2 innerhalb der Milieus auf 10,0 insgesamt. Das passt zu 2.0 und 2a: Die Twin-Milieus liegen weiter auseinander.

**Was die Abbildung aussagt:** Die simulierte Population **wirkt vielfältig, ist es aber nicht**. Ihre Breite entsteht überwiegend durch das Auslosen der Antworten. Die eigentlichen Einschätzungen des Modells, die Erwartungswerte, liegen viel enger beieinander als die echten Menschen. Zusätzlich streuen die Twins nicht nur stärker, sondern auch **anders**: Die Wertewolke hat eine andere Form, und die Werte hängen anders zusammen als bei den Personen.

**Kernerkenntnis – der Varianzkollaps gilt für die ganze Population:** Das Ergebnis aus 1e bestätigt sich über alle 10 Werte hinweg. Das Modell unterscheidet die Twins deutlich weniger, als sich echte Menschen unterscheiden. Die scheinbare Vielfalt ist geliehen vom Zufall der Ziehung.

**Einschränkung:** Auch die Antworten der Personen sind eine einzelne Antwort mit Messfehler, ihre Streuung enthält also ebenfalls etwas Zufall. Der Vergleich mit den Erwartungswerten der Twins überzeichnet den Kollaps deshalb etwas; die gezogenen Antworten sind der Vergleich Antwort gegen Antwort. Die Halbierung der Streuung lässt sich damit aber nicht allein erklären.

*N = 2 262 Personen, 10 zentrierte Werte aus gezogenen Antworten bzw. Erwartungswerten; Milieus wie in 2.1. Bures-Wasserstein-Distanz der Kovarianzmatrizen (gezogene Antworten); Rauschen: Distanz zweier Zufallshälften der Personen.*
