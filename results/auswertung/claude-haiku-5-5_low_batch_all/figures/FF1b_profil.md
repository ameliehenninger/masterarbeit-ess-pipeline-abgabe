# 1b – Trifft der Twin, was seiner Person wichtig ist?

Datei: `FF1b_profil.png`

Jede der 2 262 Personen hat 21 Fragen zu ihren Werten beantwortet, etwa wie wichtig ihr Tradition, Erfolg, Hilfsbereitschaft oder Abenteuer ist. Daraus ergibt sich für jede Person eine **Rangfolge**: Manche Dinge sind ihr sehr wichtig, andere kaum. Ihr Twin hat dieselben 21 Fragen beantwortet (siehe 1a).

Abbildung 1a hat gemessen, *wie weit* die Antworten daneben liegen. Abbildung 1b zeigt, ob der Twin die **Reihenfolge** trifft: Hält er für wichtig, was die Person für wichtig hält, und für unwichtig, was sie für unwichtig hält?

## Welche Maße verwendet werden und warum

**Rangkorrelation nach Spearman (ρ).** Für jedes Paar aus Person und Twin werden die 21 Antworten jeweils der Größe nach geordnet. Dann wird geprüft, wie gut die beiden Rangfolgen übereinstimmen. Das Ergebnis wird über alle Paare gemittelt. **ρ = 1** heißt, die Rangfolge ist identisch; **ρ = 0** heißt, es gibt keinen Zusammenhang; negative Werte hießen, die Rangfolge ist umgekehrt. **Ein höherer Balken bedeutet eine bessere Übereinstimmung.**

*Warum Spearman?* Ein Twin kann das Niveau verfehlen, etwa weil er generell zurückhaltender antwortet, und trotzdem die Rangfolge treffen. Der MAE aus 1a würde ihn dafür bestrafen, ρ nicht. Spearman rechnet außerdem nur mit Rangplätzen. Das passt zu einer Antwortskala, bei der nicht sicher ist, dass der Abstand von 1 zu 2 genauso groß ist wie der von 5 zu 6.

**Bereinigung um das allgemeine Muster (rechte Gruppe).** Viele Werte sind in der Bevölkerung fast allen wichtig (etwa anderen helfen, Freunden gegenüber loyal sein), andere fast allen unwichtig (etwa reich sein). Wer nur dieses allgemeine Muster kennt, trifft die Rangfolge schon recht gut, ohne die Person zu kennen. Deshalb wird für jede Frage die Durchschnittsantwort aller Personen abgezogen, bei der Person und ebenso beim Twin. Übrig bleibt nur, was die Person **von der Bevölkerung unterscheidet**: Was ist ihr wichtiger als den meisten anderen, was weniger wichtig? Erst darauf wird ρ berechnet.

*Warum?* Nur so lässt sich prüfen, ob der Twin etwas über *diese eine* Person weiß und nicht bloß über Menschen in Deutschland im Allgemeinen.

**Vergleichsgrößen.** Wie in 1a wird der Twin mit Vorhersagen verglichen, die nichts über die einzelne Person wissen: dem **fremden Twin** (hellgrau), also dem Twin einer anderen, zufällig gewählten Person, und dem **Demografie-Mittelwert** (dunkelgrau), also den Durchschnittsantworten der anderen Personen mit gleichem Geschlecht, gleicher Altersgruppe und gleichem Bildungsabschluss.

**Erwartungswerte.** Wie in 1a werden für den Twin und den fremden Twin die Erwartungswerte verwendet, nicht die gezogenen Antworten. Die Ziehung fügt Zufall hinzu, der die Rangfolge verwischt und nichts über die Person verrät.

**Wilcoxon-Test.** Er prüft wie in 1a für jede Person einzeln, ob der eigene Twin oder der fremde Twin besser abschneidet, und ob der eigene Twin über alle Personen hinweg gesichert vorne liegt. Auf dieselbe Weise wird der Twin mit dem Demografie-Mittelwert verglichen.

## Was die Abbildung zeigt

**Die linke Gruppe** zeigt die Übereinstimmung im ganzen Werteprofil:

- **Twin: ρ = 0,50.** Das klingt zunächst ordentlich.
- **Fremder Twin: ρ = 0,40.** Er weiß nichts über die Person und erreicht trotzdem einen großen Teil davon. Ein großer Teil der Übereinstimmung stammt also aus dem allgemeinen Muster.
- **Demografie-Mittelwert: ρ = 0,58.** Er liegt über dem Twin, weil er das allgemeine Muster der echten Antworten genau kennt.

**Die rechte Gruppe** zeigt die Übereinstimmung nach Abzug des allgemeinen Musters, also nur die individuelle Abweichung der Person:

- **Fremder Twin: ρ = 0,00.** Ohne das allgemeine Muster weiß er nichts mehr über die Person. Das bestätigt, dass die Bereinigung funktioniert. Er erscheint deshalb nur als Zahl, nicht als Balken.
- **Twin: ρ = 0,19.** Klein, aber klar über null (Wilcoxon-Test gegen den fremden Twin, p < 0,001). Bei 75 % der Twins ist der Wert positiv.
- **Demografie-Mittelwert: ρ = 0,17.** Etwas niedriger als beim Twin. 51 % der Twins schneiden besser ab als ihr Demografie-Mittelwert. Der Vorsprung ist statistisch knapp gesichert (Wilcoxon-Test je Person gepaart, p = 0,016), praktisch aber vernachlässigbar: Die mittlere Differenz beträgt 0,02 (Effektstärke dz = 0,07), und ein Vorzeichentest (51 % besser, p = 0,17) findet keinen Unterschied. Bei 2 262 Personen werden auch sehr kleine Unterschiede signifikant.

**Was die Abbildung aussagt:** Der Twin enthält **echte Information über seine Person**, die über das allgemeine Wertemuster der Bevölkerung hinausgeht. Bei der individuellen Abweichung ist sie **etwa so groß** wie das, was allein Geschlecht, Alter und Bildung verraten, wenn man die Antworten ähnlicher echter Personen kennt. Der Vorsprung ist aber klein (0,19 gegenüber 0,17), obwohl das Profil des Twins zusätzlich Wohnort, Religion, politische Einstellung und weitere Angaben enthält.

**Kernerkenntnis – Rangfolge ja, Niveau nein:** Im ganzen Profil liegt der Twin hinter dem Demografie-Mittelwert, bei der individuellen Abweichung gleichauf. Der Twin weiß also, was *dieser* Person wichtiger oder unwichtiger ist als anderen, verschiebt aber das ganze Profil in eine Richtung (siehe 1c). Das erklärt auch, warum er beim MAE in 1a verliert: Der MAE bestraft die Verschiebung, ρ nach Abzug des Musters nicht.

**Erwartungswert und Ziehung:** Mit gezogenen Antworten wären es nur ρ = 0,36 im ganzen Profil und 0,12 bei der individuellen Abweichung; dann läge der Twin auch rechts unter dem Demografie-Mittelwert (0,17). Das Rauschen der Ziehung verdeckt also einen Teil dessen, was das Modell über die Person weiß. **Die Rangfolge Twin gegenüber Demografie-Mittelwert hängt damit von der Wahl Erwartungswert/Ziehung ab** (in allen 20 neuen Ziehungen gleich); dass der Twin Information über die Person enthält, gilt in beiden Varianten. Vollständig: Sensitivitätsanalyse im Report-Anhang und DOKUMENTATION.md 5.6.

*N = 2 262 Personen, je 21 Fragen, Erwartungswerte der Twins. Rechte Gruppe, Wilcoxon-Test je Person gepaart: Twin gegenüber fremdem Twin p < 0,001, Twin gegenüber Demografie-Mittelwert p = 0,016.*
