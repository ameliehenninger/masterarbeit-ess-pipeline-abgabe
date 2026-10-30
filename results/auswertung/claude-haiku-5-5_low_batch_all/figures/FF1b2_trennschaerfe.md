# 1b′ – Unterscheidet der Twin die Personen bei einer Frage?

Datei: `FF1b2_trennschaerfe.png`

Abbildung 1b hat für jede **Person** gefragt, ob ihr Twin die Rangfolge ihrer 21 Werte trifft. Abbildung 1b′ dreht die Blickrichtung um: Sie nimmt **eine Frage** und fragt, ob der Twin die 2 262 Personen bei dieser Frage richtig auseinanderhält. Bekommt also die Person, der Tradition besonders wichtig ist, auch einen Twin, der Tradition für besonders wichtig hält?

## Welche Maße verwendet werden und warum

**Spearman ρ je Frage.** Für eine Frage werden die Antworten aller Personen und die ihrer Twins jeweils der Größe nach geordnet und die beiden Rangfolgen verglichen. **ρ = 1** heißt, der Twin ordnet die Personen genau so wie ihre echten Antworten; **ρ = 0** heißt, die Antwort des Twins verrät nichts darüber, wo die Person im Vergleich zu den anderen steht.

*Warum?* Das ist die Frage, die eine Forscherin stellt, die mit Twins Zusammenhänge untersuchen will: Sind die Twins bei einer Frage richtig sortiert? Ein Twin kann bei allen Personen zu niedrig liegen (1c) und sie trotzdem richtig sortieren.

**Demografie-Mittelwert (Punkt).** Die Durchschnittsantwort der anderen Personen mit gleichem Geschlecht, gleicher Altersgruppe und gleichem Bildungsabschluss. Er sortiert die Personen nur nach diesen drei Merkmalen.

**Gepaarter Bootstrap.** Die Personen werden 1 000-mal mit Zurücklegen neu gezogen. In jeder Stichprobe werden ρ für den Twin und ρ für den Demografie-Mittelwert auf denselben Personen berechnet, dazu ihre Differenz. Die mittleren 95 % dieser Werte bilden das Intervall.

*Warum?* Bei 21 Fragen liegen manche Unterschiede bei wenigen Hundertsteln. Erst das Intervall der Differenz zeigt, ob der Twin bei einer Frage **gesichert** besser ist oder ob der Unterschied Zufall der Stichprobe sein könnte. „Gepaart“ heißt: Weil beide Größen auf denselben Personen beruhen, wird ihre Differenz direkt geprüft und nicht zwei getrennte Intervalle verglichen.

## Was die Abbildung zeigt

**Jeder Balken** ist das ρ des Twins für eine Frage, **die schwarze Linie** sein 95-%-Intervall, **der graue Punkt** das ρ des Demografie-Mittelwerts. **Kräftig** heißt: Der Twin ist gesichert besser (das Intervall der Differenz liegt über 0). **Blass** heißt: nicht gesichert verschieden. **Blass und schraffiert** heißt: gesichert schlechter (das Intervall der Differenz liegt unter 0). **Die beiden Zahlenspalten rechts** nennen die Werte von Twin und Demografie-Mittelwert („Demo.“).

- **Gesichert besser bei 14 von 21 Fragen.** Den größten Vorsprung gegenüber dem Demografie-Mittelwert hat der Twin bei Tradition (+0,28), Umwelt schützen (+0,20) und starker Staat (+0,14). Abenteuer hat zwar das dritthöchste ρ (0,38), aber nur +0,07 Vorsprung, weil schon die Demografie hier gut sortiert (0,31).
- **Nicht unterscheidbar bei 6 Fragen:** reich sein, Fähigkeiten zeigen, bescheiden sein, Spaß haben, frei entscheiden und Freunden loyal.
- **Gesichert schlechter bei 1 Frage:** Vergnügen (0,11 gegen 0,19), in der Abbildung schraffiert.
- **Insgesamt schwach:** Kein ρ erreicht 0,5. Ein ρ von 0,3 gilt als schwacher Zusammenhang.

**Was die Abbildung aussagt:** Bei den meisten Fragen sortiert der Twin die Personen etwas besser, als Geschlecht, Alter und Bildung allein es könnten. Am besten gelingt das bei Themen, die eng mit Angaben im Profil zusammenhängen: Tradition (Religion, Alter), Umwelt und starker Staat (politische Einstellung). Bei Werten wie Vergnügen und Spaß, die das Modell ohnehin unterschätzt (1c), hilft das Profil kaum.

**Kernerkenntnis – der Twin nutzt das Profil, wo es naheliegt:** Der Vorsprung des Twins entsteht dort, wo das Profil einen direkten Hinweis enthält. Das passt zu Fazit 3: Das Modell leitet Werte stark aus den Profilangaben ab.

**Einschränkung:** Bei 21 Fragen ist mit einzelnen Zufallsbefunden zu rechnen; die Intervalle sind nicht für mehrfaches Testen korrigiert. Die großen Abstände (Tradition, Umwelt, starker Staat) sind davon nicht betroffen. Mit gezogenen statt Erwartungswerten wäre der Twin nur bei 10 Fragen besser (Punktschätzer), weil die Ziehung die Rangfolge verwischt, gesichert besser nur bei 3 und gesichert schlechter bei 6. Die Aussage „trennschärfer als die Demografie“ hängt also von der Wahl Erwartungswert/Ziehung ab (Sensitivitätsanalyse, DOKUMENTATION.md 5.6).

*N = 2 262 Personen, Erwartungswerte der Twins. Spearman ρ je Frage über alle Personen; 95-%-Intervalle aus 1 000 gepaarten Bootstrap-Stichproben der Personen.*
