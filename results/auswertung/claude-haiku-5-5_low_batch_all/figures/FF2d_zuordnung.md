# 2d – Landet der Twin im Milieu seiner Person?

Datei: `FF2d_zuordnung.png`

Die Abbildungen 2a bis 2c haben die Populationen als Ganzes verglichen. Abbildung 2d verbindet Ebene 2 wieder mit Ebene 1. Wenn der Twin seine Person kennt, sollte ein offener Mensch auch einen offenen Twin haben.

Die Abbildung zeigt für alle Paare aus Person und Twin, ob der Twin im selben Milieu landet wie seine Person.

## Welche Maße verwendet werden und warum

**Trefferquote.** Der Anteil der Paare, bei denen Person und Twin im selben Milieu sind.

*Warum?* Sie ist die anschaulichste Zahl. Allein täuscht sie aber, weil man auch durch Raten einen Teil richtig hätte.

**Zufallserwartung.** Sie gibt an, wie viele Treffer sich ergeben würden, wenn die Twins *ohne jeden Bezug* zu ihrer Person auf die Milieus verteilt würden, in denselben Größen wie tatsächlich: Anteil der Personen × Anteil der Twins je Milieu, summiert.

*Warum?* Der Vergleichsmaßstab ist nicht 0 %, sondern das, was Raten erreicht. Das entspricht der Logik des fremden Twins in 1a.

**Adjusted Rand Index (ARI).** Der ARI ist das übliche Maß für die Übereinstimmung zweier Gruppierungen. Er betrachtet alle Paare von Personen und fragt: Wenn zwei Personen im selben Milieu sind, sind dann auch ihre Twins im selben Milieu, und umgekehrt? „Adjusted“ heißt, dass die zufällige Übereinstimmung bereits abgezogen ist. **ARI = 0 heißt: nicht besser als Zufall. ARI = 1 heißt: perfekte Übereinstimmung.**

*Warum zusätzlich?* Anders als die Trefferquote hängt der ARI nicht von den Gruppengrößen ab und muss die Milieus beider Seiten nicht einander zuordnen. Ob er über dem Zufall liegt, wird wie in 2c mit 500 zufälligen Vertauschungen geprüft.

Ob ein Milieu besser getroffen wird als das andere, zeigen direkt die Zeilenprozente der Tafel; ein eigenes Maß je Milieu (etwa der Jaccard-Index) ist dafür nicht nötig.

## Was die Abbildung zeigt

**Die Abbildung ist eine Kreuztabelle.** **Zeilen** sind das Milieu der Person, **Spalten** das Milieu des Twins. **Die Diagonale** (oben links, unten rechts) sind Treffer. **Die Prozentzahl** ist der Anteil an der Zeile: „51 %“ oben links heißt, von allen Personen im offenen Milieu landen 51 % der Twins ebenfalls im offenen Milieu. **Die Farbe** wird mit dem Anteil dunkler (ohne eigene Farbskala, die Zahl steht in jeder Zelle). **Die Summen** zeigen rechts die Zahl der Personen, unten die Zahl der Twins je Milieu.

- **Trefferquote 62 %** ((639 + 757) / 2 262). Bei Zufall wären es 0,55 × 0,39 + 0,45 × 0,61 = **49 %**. Das ist ein Vorsprung von 13 Prozentpunkten.
- **Beide Milieus gleich schwach.** Der Zufallswert je Zeile ist der Anteil der Twins im jeweiligen Milieu: Würden die Twins ohne Bezug zu ihrer Person verteilt, landeten 39 % jeder Zeile im offenen und 61 % im bewahrenden Milieu.
- **Milieu 1 (offen): 51 % statt 39 %.** Von den offenen Personen haben 51 % einen offenen Twin, **12 Prozentpunkte** über dem Zufall.
- **Milieu 2 (bewahrend): 75 % statt 61 %.** Das wirkt besser, liegt aber nur **14 Prozentpunkte** über dem Zufall. Die hohe Zahl entsteht vor allem dadurch, dass die Twins ohnehin mehrheitlich im bewahrenden Milieu landen (61 % aller Twins, siehe 2.1).
- **ARI = 0,05.** Das liegt gesichert über dem Zufall (95 % der Vertauschungen liegen unter 0,002), aber nahe 0.
- **Robustheit:** Mit k-Means statt LPA ist der ARI 0,08; ordnet man die Twins mit dem Modell der Personen zu, ist er 0,06.
- **Nicht die Ziehung ist schuld:** Bildet man die Milieus der Twins aus den Erwartungswerten statt aus den gezogenen Antworten, landen 63 % im Milieu ihrer Person (ARI 0,07), kaum mehr als mit Ziehung.

**Was die Abbildung aussagt:** Der Twin landet **kaum öfter im Milieu seiner Person, als es der Zufall erwarten lässt**. Das Ergebnis aus Ebene 1 zeigt sich damit auch auf Ebene der Milieus: Der Twin trägt **ein wenig** Information über seine Person (1b: ρ = 0,19 nach Abzug des allgemeinen Musters), aber zu wenig, um sie verlässlich der richtigen Wertegruppe zuzuordnen. Das gilt für beide Milieus gleichermaßen. Dass offene Personen absolut seltener richtig landen (51 % gegen 75 %), passt zu 1d (offene Personen trifft der Twin am schlechtesten) und zu 1c (das Modell unterschätzt Spaß, Erfolg, Kreativität und Abwechslung).

**Kernerkenntnis – richtige Milieus, falsche Menschen:** Selbst wenn die Milieus in der simulierten Population grob ähnlich aussehen (2.1, 2a), bestehen sie **nicht aus den richtigen Menschen**. Eine Auswertung, die fragt, *wer* zu einem Milieu gehört (zum Beispiel nach Alter, Bildung oder Region), käme mit den Twins zu anderen Ergebnissen als mit den echten Befragten.

**Einschränkung:** Die Milieus sind Regionen in einem Kontinuum (siehe 2.0). Personen nahe der Grenze zwischen den Milieus können schon durch kleine Abweichungen auf der anderen Seite landen. Das senkt die Trefferquote. Dass sie trotzdem kaum über dem Zufall liegt und der ARI mit allen Verfahren nahe 0 bleibt, spricht aber dafür, dass der Befund nicht nur daran liegt.

*N = 2 262 Paare aus Person und Twin, gezogene Antworten. Milieus: LPA mit k = 2, getrennt für Personen und Twins (siehe 2.1). ARI gegen 500 zufällige Vertauschungen; Robustheit mit k-Means und mit Zuordnung der Twins im Personen-Modell.*
