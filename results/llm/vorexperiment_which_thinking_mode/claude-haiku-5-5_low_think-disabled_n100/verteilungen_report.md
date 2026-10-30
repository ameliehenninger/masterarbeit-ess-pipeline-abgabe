# Verteilungsanalyse: claude-haiku-5-5_low_think-disabled_n100

100 Personen × 21 Fragen = 2100 Wahrscheinlichkeitsvektoren. Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).

## 1. Form der Vektoren

| Kennzahl | Wert |
|---|---|
| Entropie Mittel (Median; 10.–90. Perzentil) | 2,032 Bit (2,081; 1,626–2,361) |
| Entropie relativ zur Gleichverteilung (2,585 Bit) | 78,6 % |
| höchste Wahrscheinlichkeit, Mittel | 0,388 |
| Masse der zwei wahrscheinlichsten Optionen | 0,679 |
| Anteil scharfer Vektoren (max p ≥ 0,80) | 0,1 % |
| Anteil One-Hot (max p ≥ 0,99) | 0,0 % |
| Anteil flacher Vektoren (≥ 90 % der Höchstentropie) | 16,3 % |
| Anteil eingipfliger Vektoren | 100,0 % |
| SD innerhalb eines Vektors | 1,127 Skalenpunkte |
| Rohwerte auf 0,05-Raster / 0,1-Raster | 62,9 % / 36,1 % |
| größte Abweichung der Rohsumme von 1 | 0,000 |

## 2. Unterscheidet das Modell die Personen?

| Kennzahl | Wert |
|---|---|
| verschiedene Vektoren | 453 von 2100 (21,6 %) |
| häufigster Vektor | 0,3 / 0,4 / 0,2 / 0,07 / 0,02 / 0,01 (3,7 % aller Vektoren) |
| verschiedene Vektoren je Frage (von 100 Personen, Mittel) | 55,3 |
| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | 62,3 % |
| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | 0,116 |
| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | 0,704 |

## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell

| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch 1,116) |
|---|---|---|---|
| (a) nur wahrscheinlichste Option | 0,111 | 0,562 | 0,974 |
| (b) Mittel der vollen Vektoren | 0,052 | 0,465 | 1,351 |
| (c) gezogene Antwort (Pipeline) | 0,055 | 0,472 | 1,321 |

Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): Q10 `ipgdtima` (JS 0,109), Q13 `ipsucesa` (JS 0,103), Q14 `ipstrgva` (JS 0,094).

Abbildung: `figures/plot4_verteilungen.png`. Je Frage alle Werte: `verteilungen_items.csv`.
