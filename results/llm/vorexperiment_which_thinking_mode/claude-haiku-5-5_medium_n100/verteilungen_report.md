# Verteilungsanalyse: claude-haiku-5-5_medium_n100

100 Personen × 21 Fragen = 2100 Wahrscheinlichkeitsvektoren. Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).

## 1. Form der Vektoren

| Kennzahl | Wert |
|---|---|
| Entropie Mittel (Median; 10.–90. Perzentil) | 2,041 Bit (2,126; 1,580–2,360) |
| Entropie relativ zur Gleichverteilung (2,585 Bit) | 79,0 % |
| höchste Wahrscheinlichkeit, Mittel | 0,382 |
| Masse der zwei wahrscheinlichsten Optionen | 0,670 |
| Anteil scharfer Vektoren (max p ≥ 0,80) | 0,5 % |
| Anteil One-Hot (max p ≥ 0,99) | 0,0 % |
| Anteil flacher Vektoren (≥ 90 % der Höchstentropie) | 15,8 % |
| Anteil eingipfliger Vektoren | 100,0 % |
| SD innerhalb eines Vektors | 1,112 Skalenpunkte |
| Rohwerte auf 0,05-Raster / 0,1-Raster | 74,3 % / 45,0 % |
| größte Abweichung der Rohsumme von 1 | 0,000 |

## 2. Unterscheidet das Modell die Personen?

| Kennzahl | Wert |
|---|---|
| verschiedene Vektoren | 724 von 2100 (34,5 %) |
| häufigster Vektor | 0,4 / 0,35 / 0,15 / 0,05 / 0,03 / 0,02 (1,9 % aller Vektoren) |
| verschiedene Vektoren je Frage (von 100 Personen, Mittel) | 73,8 |
| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | 41,9 % |
| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | 0,122 |
| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | 0,675 |

## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell

| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch 1,116) |
|---|---|---|---|
| (a) nur wahrscheinlichste Option | 0,086 | 0,524 | 0,948 |
| (b) Mittel der vollen Vektoren | 0,059 | 0,516 | 1,319 |
| (c) gezogene Antwort (Pipeline) | 0,066 | 0,521 | 1,297 |

Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): Q10 `ipgdtima` (JS 0,181), Q14 `ipstrgva` (JS 0,126), Q13 `ipsucesa` (JS 0,112).

Abbildung: `figures/plot4_verteilungen.png`. Je Frage alle Werte: `verteilungen_items.csv`.
