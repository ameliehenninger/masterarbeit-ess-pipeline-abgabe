# ess_scores.csv

- **Eingabedatei:** `ESS_fragebogen_DE.csv`
- **Erzeugt mit:** `ess_pipeline.scoring`
- **hedonism_to:** `openness`
- **Zeilen:** 2262 (Reihenfolge wie Eingabedatei)
- **Werte:** ungerundet, volle Gleitkomma-Genauigkeit

## Spalten

| Spalte | Bedeutung |
|---|---|
| `id` | Personen-ID (als String, identisch zur Eingabe) |
| `MRAT` | Individueller Antwortstil: Mittel aller 21 umgepolten Items |
| `SD` | Self-Direction / Selbstbestimmung (MRAT-zentriert) |
| `ST` | Stimulation / Stimulation (MRAT-zentriert) |
| `HE` | Hedonism / Hedonismus (MRAT-zentriert) |
| `AC` | Achievement / Leistung (MRAT-zentriert) |
| `PO` | Power / Macht (MRAT-zentriert) |
| `SE` | Security / Sicherheit (MRAT-zentriert) |
| `CO` | Conformity / Konformität (MRAT-zentriert) |
| `TR` | Tradition / Tradition (MRAT-zentriert) |
| `BE` | Benevolence / Wohlwollen (MRAT-zentriert) |
| `UN` | Universalism / Universalismus (MRAT-zentriert) |
| `OPEN` | Openness to Change / Offenheit für Wandel (MRAT-zentriert) |
| `CONS` | Conservation / Bewahrung (MRAT-zentriert) |
| `SELFENH` | Self-Enhancement / Selbststärkung (MRAT-zentriert) |
| `SELFTRANS` | Self-Transcendence / Selbsttranszendenz (MRAT-zentriert) |
| `x` | SELFTRANS − SELFENH (> 0: Fokus auf andere/Gemeinwohl; < 0: eigener Erfolg/Status) |
| `y` | OPEN − CONS (> 0: Wandel/Unabhängigkeit; < 0: Sicherheit/Tradition) |

## Antwortskala (roh)

1 = Very much like me, 2 = Like me, 3 = Somewhat like me, 4 = A little like me, 5 = Not like me, 6 = Not like me at all. Keine invertierten Items.

## Formeln

**Stufe 1 – Umpolen:** `x' = 7 − x` für alle 21 Items (danach 6 = sehr wichtig, 1 = gar nicht wichtig).

**Stufe 2 – MRAT:** `MRAT = (Summe aller 21 umgepolten Items) / 21`

**Stufe 3 – Basiswerte:** `Wert = Mittelwert der umgepolten Items − MRAT`

| Spalte | Formel |
|---|---|
| `SD` | (ipcrtiva' + impfreea') / 2 − MRAT |
| `ST` | (impdiffa' + ipadvnta') / 2 − MRAT |
| `HE` | (ipgdtima' + impfuna') / 2 − MRAT |
| `AC` | (ipshabta' + ipsucesa') / 2 − MRAT |
| `PO` | (impricha' + iprspota') / 2 − MRAT |
| `SE` | (impsafea' + ipstrgva') / 2 − MRAT |
| `CO` | (ipfrulea' + ipbhprpa') / 2 − MRAT |
| `TR` | (ipmodsta' + imptrada') / 2 − MRAT |
| `BE` | (iphlppla' + iplylfra') / 2 − MRAT |
| `UN` | (ipeqopta' + ipudrsta' + impenva') / 3 − MRAT |

**Stufe 4 – Higher-Order Values:** ungewichtetes Mittel der (bereits MRAT-zentrierten) Basiswerte; jeder Basiswert zählt gleich, unabhängig von seiner Item-Zahl.

| Spalte | Basiswerte | Items | Formel |
|---|---|---|---|
| `OPEN` | SD, ST, HE | 6 (ipcrtiva, impfreea, impdiffa, ipadvnta, ipgdtima, impfuna) | (SD + ST + HE) / 3 |
| `CONS` | SE, CO, TR | 6 (impsafea, ipstrgva, ipfrulea, ipbhprpa, ipmodsta, imptrada) | (SE + CO + TR) / 3 |
| `SELFENH` | AC, PO | 4 (ipshabta, ipsucesa, impricha, iprspota) | (AC + PO) / 2 |
| `SELFTRANS` | UN, BE | 5 (ipeqopta, ipudrsta, impenva, iphlppla, iplylfra) | (UN + BE) / 2 |

Hinweis: Nach dem Mitteln der zentrierten Basiswerte wird **kein** weiteres MRAT abgezogen (das wäre eine doppelte Zentrierung).

Hedonism-Zuordnung (`hedonism_to`): `openness` = HE zählt zu OPEN (Default, Schwartz' Scoring Key für ESS); `both` = HE zählt zu OPEN und SELFENH; `none` = HE zählt zu keinem Higher-Order Value.

**Stufe 5 – Koordinaten:** `x = SELFTRANS − SELFENH`, `y = OPEN − CONS`. Keine erneute Zentrierung (MRAT kürzt sich heraus).

## Identitäten (geprüft in `ess_pipeline.validation`)

- `2·SD + 2·ST + 2·HE + 2·AC + 2·PO + 2·SE + 2·CO + 2·TR + 2·BE + 3·UN = 0` für jede Person
- `MRAT = 7 − Zeilenmittel der Roh-Items`
