# 2.0 – Gibt es überhaupt getrennte Milieus?

Datei: `FF2_0_milieus_existenz.png`

Die Abbildungen 1a bis 1e haben jeden Twin mit *seiner* Person verglichen (Ebene 1). Ab hier geht es um **Ebene 2**: Bildet die simulierte Population als Ganzes dieselbe Struktur wie die echte? Konkret: Teilen sich Menschen in **Werte-Milieus** auf, also in Gruppen mit ähnlichen Wertehaltungen, und finden sich dieselben Gruppen bei den Twins?

Bevor man Milieus vergleicht, muss geklärt sein, ob es sie überhaupt gibt. Die Abbildung zeigt, wie klar sich Personen und Twins in Gruppen trennen lassen.

## Welche Maße verwendet werden und warum

**10 zentrierte Werte.** Auf Ebene 2 werden nicht mehr die 21 einzelnen Fragen betrachtet, sondern die **10 Grundwerte nach Schwartz** (Selbstbestimmung, Stimulation, Hedonismus, Leistung, Macht, Sicherheit, Konformität, Tradition, Wohlwollen, Universalismus). Jeder Grundwert ist das Mittel aus zwei oder drei Fragen. Davon wird der **persönliche Durchschnitt** über alle 21 Fragen abgezogen. Ein zentrierter Wert von +1 heißt: Dieser Wert ist der Person einen Skalenpunkt wichtiger als ihre Werte im Durchschnitt.

*Warum zentrieren?* Manche Menschen kreuzen generell hohe Werte an, andere generell niedrige. Nach Schwartz zählt aber nur, was einer Person **im Vergleich zu ihren anderen Werten** wichtig ist. Die Zentrierung entfernt den persönlichen Antwortstil.

**k-Means.** Ein Gruppierungsverfahren, das die Personen in eine vorgegebene Zahl von Gruppen **k** aufteilt, sodass die Personen innerhalb einer Gruppe möglichst nah beieinander liegen. Es findet **immer** Gruppen, auch in Daten, in denen es keine gibt.

**Silhouette.** Sie misst, ob die gefundenen Gruppen echt sind. Für jede Person wird verglichen, wie nah sie an ihrer eigenen Gruppe liegt und wie nah an der nächsten anderen Gruppe. Gemittelt ergibt sich ein Wert zwischen 0 und 1. **0** heißt, die Gruppen gehen fließend ineinander über; **1** heißt, sie sind perfekt getrennt, wie Inseln.

**Zufallsdaten ohne Gruppen.** Auch in Daten ganz ohne Gruppen ergibt sich keine Silhouette von genau 0. Deshalb werden künstliche Daten erzeugt, die dieselbe Streuung und dieselben Zusammenhänge zwischen den Werten haben wie die echten Personen, aber aus einer einzigen Normalverteilung stammen und deshalb **garantiert keine Gruppen** enthalten.

*Warum?* Sie zeigen, welche Silhouette man ohne jede Gruppenstruktur erhält. Sie erfüllen damit dieselbe Aufgabe wie die Vergleichsgrößen in 1a: Nur was deutlich darüber liegt, ist echte Gruppenstruktur.

Die Zufallsdaten werden **zweimal** gebildet: einmal mit der Streuung und den Zusammenhängen der Personen (grau), einmal mit denen der Twins (hellorange). *Warum?* Die Silhouette hängt auch davon ab, wie die Wertewolke geformt ist; eine länglichere Wolke lässt sich leichter in zwei Hälften teilen, auch ohne echte Gruppen. Die Twins müssen sich deshalb an ihren eigenen Zufallsdaten messen lassen.

## Was die Abbildung zeigt

**Die x-Achse** zeigt die Zahl der Gruppen k (2 bis 8), **die y-Achse** die Silhouette. **Blau** sind die Personen, **orange** die Twins, **grau gestrichelt** die Zufallsdaten nach Vorbild der Personen, **hellorange gestrichelt** die nach Vorbild der Twins (je Mittel aus 5 Ziehungen).

**Die blaue Linie** liegt bei allen k **genau auf der grauen Linie**. Bei k = 2 beträgt die Silhouette 0,163, bei den Zufallsdaten 0,162. Die Werte der echten Personen bilden also **keine getrennten Gruppen**, sondern ein **Kontinuum**.

**Die orange Linie** liegt bei k = 2 mit **0,24** deutlich höher als die Personen. Ein Teil davon liegt aber an der Form der Twin-Wolke: Auch die Zufallsdaten nach Vorbild der Twins erreichen schon **0,20**. Über diesem eigenen Vergleichswert liegen die Twins nur noch um 0,04. Die Twins spalten sich also **etwas** klarer in zwei Lager, als es ihre Form allein erklärt. Ab k = 3 verschwindet der Unterschied. Rechnet man die Twins mit Erwartungswerten statt mit gezogenen Antworten, steigt ihre Silhouette bei k = 2 sogar auf **0,44**: Die Ziehung verwischt die Spaltung nur, sie erzeugt sie nicht.

Eine zweite Prüfung bestätigt das Ergebnis für die Personen: Die Latent-Profile-Analyse (siehe 2.1) bevorzugt bei voller Berücksichtigung der Zusammenhänge zwischen den Werten **eine einzige Gruppe** (k = 1), also ebenfalls keine Milieus.

**Was die Abbildung aussagt:** Bei den Personen gibt es keine natürlichen Milieus. Für den Vergleich in 2.1 bis 2d wird trotzdem **k = 2 fest gesetzt**, weil zwei Gruppen den deutlichsten Vergleich erlauben und bei den Personen die höchste Silhouette haben. Die zwei „Milieus“ sind deshalb als **Regionen in einem Kontinuum** zu lesen, etwa „eher offen“ und „eher bewahrend“, und nicht als scharf getrennte Gruppen.

**Kernerkenntnis – das Modell überzeichnet Gegensätze:** Dass sich die Twins klarer in zwei Lager teilen, ist selbst ein Befund, wenn auch kleiner, als der Vergleich mit den Personen allein nahelegt. Das Modell ordnet Personen eher einem klaren Typ zu, als es die Wirklichkeit hergibt. Das passt zu 1c (systematischer Bias in Richtung bestimmter Werte) und zu Fazit 3, wonach das Modell Werte stärker aus der Demografie ableitet als echte Menschen. Typisieren führt zu deutlicheren Lagern.

**Zwei Verfahren, ein Ergebnis.** Die Silhouette wird mit k-Means gerechnet, die Milieus ab 2.1 aber mit der Latent-Profile-Analyse (LPA). Für die LPA-Lösung selbst ergibt sich praktisch dieselbe Silhouette (Personen 0,16, Twins 0,24); die Aussage hängt also nicht vom Verfahren ab. Die LPA mit diagonaler Kovarianz nimmt an, dass die Werte innerhalb eines Milieus unabhängig voneinander sind. Zentrierte Werte hängen aber per Konstruktion negativ zusammen, weil der persönliche Mittelwert abgezogen ist. Mit voller Kovarianz, die diese Zusammenhänge berücksichtigt, bevorzugt die LPA bei den Personen k = 1.

**Warum trotzdem k = 2?** Weder Silhouette noch LPA finden bei den Personen getrennte Gruppen. Die Milieus in 2.1 bis 2d sind deshalb **keine natürlichen Gruppen**, sondern eine Einteilung des Kontinuums in eine offenere und eine bewahrendere Hälfte. Sie dienen als Vergleichsrahmen: Liegen die Hälften bei den Twins am selben Ort, sind sie gleich groß, landen die Twins in derselben Hälfte wie ihre Person? Diese Fragen lassen sich auch an einem Kontinuum stellen.

**Einschränkung:** Die Werte der Twins beruhen auf den gezogenen Antworten, weil Ebene 2 die simulierte Population als Datensatz betrachtet.

*N = 2 262 Personen, 10 zentrierte Werte aus gezogenen Antworten. k-Means für k = 2 bis 8. Zufallsdaten: Normalverteilung mit gleicher Kovarianz wie die Personen bzw. wie die Twins, je Mittel aus 5 Ziehungen.*
