# Verteilungsanalyse: claude-haiku-5-5_low_think-adaptive_n100

100 Personen × 21 Fragen = 2100 Wahrscheinlichkeitsvektoren. Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).

## 1. Form der Vektoren

| Kennzahl | Wert |
|---|---|
| Entropie Mittel (Median; 10.–90. Perzentil) | 2,058 Bit (2,112; 1,647–2,366) |
| Entropie relativ zur Gleichverteilung (2,585 Bit) | 79,6 % |
| höchste Wahrscheinlichkeit, Mittel | 0,380 |
| Masse der zwei wahrscheinlichsten Optionen | 0,669 |
| Anteil scharfer Vektoren (max p ≥ 0,80) | 0,1 % |
| Anteil One-Hot (max p ≥ 0,99) | 0,0 % |
| Anteil flacher Vektoren (≥ 90 % der Höchstentropie) | 20,3 % |
| Anteil eingipfliger Vektoren | 100,0 % |
| SD innerhalb eines Vektors | 1,143 Skalenpunkte |
| Rohwerte auf 0,05-Raster / 0,1-Raster | 64,4 % / 36,8 % |
| größte Abweichung der Rohsumme von 1 | 0,000 |

## 2. Unterscheidet das Modell die Personen?

| Kennzahl | Wert |
|---|---|
| verschiedene Vektoren | 424 von 2100 (20,2 %) |
| häufigster Vektor | 0,02 / 0,08 / 0,2 / 0,3 / 0,25 / 0,15 (4,0 % aller Vektoren) |
| verschiedene Vektoren je Frage (von 100 Personen, Mittel) | 53,2 |
| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | 64,8 % |
| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | 0,116 |
| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | 0,702 |

## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell

| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch 1,116) |
|---|---|---|---|
| (a) nur wahrscheinlichste Option | 0,092 | 0,536 | 0,985 |
| (b) Mittel der vollen Vektoren | 0,056 | 0,497 | 1,361 |
| (c) gezogene Antwort (Pipeline) | 0,057 | 0,499 | 1,331 |

Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): Q10 `ipgdtima` (JS 0,148), Q14 `ipstrgva` (JS 0,108), Q8 `ipudrsta` (JS 0,101).

Abbildung: `figures/plot4_verteilungen.png`. Je Frage alle Werte: `verteilungen_items.csv`.
