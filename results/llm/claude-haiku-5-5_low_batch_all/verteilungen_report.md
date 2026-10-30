# Verteilungsanalyse: claude-haiku-5-5_low_batch_all

2262 Personen × 21 Fragen = 47502 Wahrscheinlichkeitsvektoren. Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).

## 1. Form der Vektoren

| Kennzahl | Wert |
|---|---|
| Entropie Mittel (Median; 10.–90. Perzentil) | 2,035 Bit (2,090; 1,627–2,362) |
| Entropie relativ zur Gleichverteilung (2,585 Bit) | 78,7 % |
| höchste Wahrscheinlichkeit, Mittel | 0,386 |
| Masse der zwei wahrscheinlichsten Optionen | 0,676 |
| Anteil scharfer Vektoren (max p ≥ 0,80) | 0,3 % |
| Anteil One-Hot (max p ≥ 0,99) | 0,0 % |
| Anteil flacher Vektoren (≥ 90 % der Höchstentropie) | 15,2 % |
| Anteil eingipfliger Vektoren | 100,0 % |
| SD innerhalb eines Vektors | 1,129 Skalenpunkte |
| Rohwerte auf 0,05-Raster / 0,1-Raster | 62,3 % / 35,3 % |
| größte Abweichung der Rohsumme von 1 | 0,005 |

## 2. Unterscheidet das Modell die Personen?

| Kennzahl | Wert |
|---|---|
| verschiedene Vektoren | 1722 von 47502 (3,6 %) |
| häufigster Vektor | 0,3 / 0,4 / 0,2 / 0,07 / 0,02 / 0,01 (3,7 % aller Vektoren) |
| verschiedene Vektoren je Frage (von 2262 Personen, Mittel) | 319,4 |
| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | 93,3 % |
| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | 0,116 |
| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | 0,709 |

## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell

| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch 1,166) |
|---|---|---|---|
| (a) nur wahrscheinlichste Option | 0,098 | 0,605 | 0,996 |
| (b) Mittel der vollen Vektoren | 0,043 | 0,471 | 1,355 |
| (c) gezogene Antwort (Pipeline) | 0,044 | 0,476 | 1,353 |

Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): Q10 `ipgdtima` (JS 0,109), Q13 `ipsucesa` (JS 0,086), Q8 `ipudrsta` (JS 0,085).

Je Frage alle Werte: `verteilungen_items.csv`.
