# Fazit 3 – Spiegeln die Twins Werte oder Demografie?

Datei: `Fazit3_werte_oder_demografie.png`

Echte Menschen unterscheiden sich in ihren Werten oft unabhängig davon, wie alt sie sind, wo sie wohnen oder welche Bildung sie haben. Ein Sprachmodell, das einen Twin aus einem Profil erzeugt, könnte dagegen **Stereotype** anwenden: „ältere, religiöse Menschen sind traditionsbewusst, junge Städter offen für Neues“.

Die Abbildung zeigt, wie stark die Werte von Personen und Twins von der Demografie abhängen.

## Welche Maße verwendet werden und warum

**Regression je Wert.** Für jeden der 10 Grundwerte nach Schwartz (zentriert, siehe 2.0) wird geprüft, wie gut sich der Wert aus sechs Merkmalen vorhersagen lässt: Geschlecht, Alter, Schulabschluss, Wohnort, Region und Religion. Die Merkmale gehen als Kategorien ein (Dummy-Kodierung).

**R² (Bestimmtheitsmaß).** Der Anteil der Unterschiede zwischen Personen in einem Wert, den die sechs Merkmale zusammen erklären. R² = 10 % heißt: 10 % der Unterschiede gehen auf die Demografie zurück, 90 % auf anderes.

*Warum?* R² ist das übliche Maß dafür, wie stark eine Größe von einer Gruppe von Merkmalen abhängt, und lässt sich zwischen Personen und Twins direkt vergleichen. Ein deutlich höheres R² bei den Twins heißt: Das Modell leitet Werte stärker aus der Demografie ab, als es bei echten Menschen der Fall ist.

**Zwei Varianten für die Twins.** Das Ergebnis hängt stark davon ab, ob die Twins mit gezogenen Antworten oder mit Erwartungswerten gerechnet werden. Deshalb stehen beide in der Abbildung:

- **Gezogene Antworten (untere Schranke):** Die Ziehung fügt Zufall hinzu, den die Demografie nicht erklären kann. Er drückt das R² der Twins nach unten.
- **Erwartungswerte (obere Schranke):** Ohne Ziehung erklärt die Demografie mehr. Verglichen werden dann aber entrauschte Twins mit Personen, deren Antworten Messfehler enthalten, was das R² der Personen drückt. Der Abstand ist damit überzeichnet.

Der wahre Abstand liegt zwischen beiden Varianten.

## Was die Abbildung zeigt

**Jede Zeile** ist ein Grundwert, sortiert nach dem R² der Twins mit Erwartungswerten. **Blau** ist das R² der Personen, **orange gefüllt** das der Twins mit gezogenen Antworten, **orange Ring** das der Twins mit Erwartungswerten. **Die gepunktete Linie** markiert den höchsten Wert der Personen (15 %, Tradition). **Rechts** steht für beide Varianten der Faktor Twin / Person.

- **Bei den Personen** erklärt die Demografie überall wenig: **4 bis 15 %**.
- **Gezogene Antworten:** Bei den Twins sind es bis zu **37 %** (Tradition), das bis zu **4,3-Fache** der Personen (Hedonismus). Bei Wohlwollen und Macht liegen Twins und Personen fast gleichauf (× 1,2); hier schließt das 95-%-Bootstrap-Intervall des Faktors die 1 ein (in der Abbildung mit * markiert).
- **Erwartungswerte:** Bei den Twins sind es **30 bis 62 %**, das **2,9- bis 9,5-Fache**. Am größten ist der Faktor bei Hedonismus (× 9,5), Selbstbestimmung (× 9,3) und Konformität (× 7,5). Die Faktoren sind aber Quotienten kleiner Zahlen und schwanken stark: Bei Selbstbestimmung reicht das 95-%-Intervall von × 6,3 bis × 12,5, weil die Demografie bei den Personen nur 4 % erklärt. Stabiler ist der Abstand in Prozentpunkten; danach liegen Hedonismus (+55), Stimulation (+49) und Konformität (+47) vorn. Diese Rangfolge nennt der Untertitel.
- **Mit Erwartungswerten** liegen die Twins bei allen 10 Werten gesichert über den Personen, mit gezogenen Antworten bei 8 von 10 (nicht bei Macht und Wohlwollen); mit gezogenen Antworten bei 6 von 10 Werten über dem höchsten Wert der Personen.

**Was die Abbildung aussagt:** Die Werte der Twins hängen **deutlich stärker von der Demografie ab** als die echter Menschen. Das Modell schließt von Alter, Bildung, Religion und Wohnort auf Werte, und zwar stärker, als es die Daten hergeben. Es überzeichnet den Zusammenhang zwischen sozialer Lage und Werten.

**Kernerkenntnis – stereotype Twins:** Das erklärt mehrere frühere Befunde. Die Twins teilen sich deutlicher in zwei Lager (2.0), weil demografisch ähnliche Twins ähnliche Werte bekommen. Die Twins unterscheiden sich in ihren Erwartungswerten wenig (A2, 1e), weil die Demografie nur wenige Kombinationen kennt. Und der Twin trifft die Rangfolge bei Themen am besten, die eng mit Profilangaben zusammenhängen (1b′).

**Einschränkung – teilweise konstruktionsbedingt:** Die sechs Merkmale stehen selbst im Profil, aus dem der Twin erzeugt wird. Die Erwartungswerte eines Twins hängen *nur* vom Profil ab; ein hohes R² ist deshalb zum Teil zu erwarten. Aussagekräftig ist, dass das Profil weitere Angaben enthält (zum Beispiel politische Einstellung und Lebenssituation) und die sechs demografischen Merkmale trotzdem einen großen Teil erklären. Aussagekräftig ist auch der Vergleich der Werte untereinander: Bei Wohlwollen und Macht bleibt der Abstand mit gezogenen Antworten klein, bei Hedonismus, Stimulation, Konformität und Tradition ist er groß.

*N = 2 243 Personen mit vollständigen Angaben, 10 zentrierte Werte. Lineare Regression je Wert auf sechs Merkmale (Dummy-kodiert). Twins aus gezogenen Antworten (untere Schranke) und aus Erwartungswerten (obere Schranke).*
