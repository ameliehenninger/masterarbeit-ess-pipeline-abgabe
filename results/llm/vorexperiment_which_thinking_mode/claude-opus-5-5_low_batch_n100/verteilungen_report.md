# Verteilungsanalyse: claude-opus-5-5_low_batch_n100

100 Personen × 21 Fragen = 2100 Wahrscheinlichkeitsvektoren. Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).

## 1. Form der Vektoren

| Kennzahl | Wert |
|---|---|
| Entropie Mittel (Median; 10.–90. Perzentil) | 2,043 Bit (2,111; 1,716–2,261) |
| Entropie relativ zur Gleichverteilung (2,585 Bit) | 79,0 % |
| höchste Wahrscheinlichkeit, Mittel | 0,380 |
| Masse der zwei wahrscheinlichsten Optionen | 0,674 |
| Anteil scharfer Vektoren (max p ≥ 0,80) | 0,0 % |
| Anteil One-Hot (max p ≥ 0,99) | 0,0 % |
| Anteil flacher Vektoren (≥ 90 % der Höchstentropie) | 2,8 % |
| Anteil eingipfliger Vektoren | 100,0 % |
| SD innerhalb eines Vektors | 1,071 Skalenpunkte |
| Rohwerte auf 0,05-Raster / 0,1-Raster | 54,6 % / 29,9 % |
| größte Abweichung der Rohsumme von 1 | 0,000 |

## 2. Unterscheidet das Modell die Personen?

| Kennzahl | Wert |
|---|---|
| verschiedene Vektoren | 702 von 2100 (33,4 %) |
| häufigster Vektor | 0,05 / 0,2 / 0,35 / 0,25 / 0,12 / 0,03 (2,6 % aller Vektoren) |
| verschiedene Vektoren je Frage (von 100 Personen, Mittel) | 72,4 |
| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | 43,0 % |
| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | 0,089 |
| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | 0,549 |

## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell

| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch 1,116) |
|---|---|---|---|
| (a) nur wahrscheinlichste Option | 0,092 | 0,445 | 0,746 |
| (b) Mittel der vollen Vektoren | 0,031 | 0,321 | 1,214 |
| (c) gezogene Antwort (Pipeline) | 0,037 | 0,336 | 1,200 |

Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): Q10 `ipgdtima` (JS 0,077), Q7 `ipfrulea` (JS 0,065), Q12 `iphlppla` (JS 0,058).

Abbildung: `figures/plot4_verteilungen.png`. Je Frage alle Werte: `verteilungen_items.csv`.
