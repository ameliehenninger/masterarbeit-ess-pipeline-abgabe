"""
Phase 3 – Analyse der vollständigen Wahrscheinlichkeitsvektoren (Verbalized Sampling).

Je Person und Frage gibt das Modell eine Verteilung p1 … p6 über die Antwortoptionen an. Wer davon nur die
wahrscheinlichste Option weiterverwendet, wirft die Unsicherheit weg und erzeugt den Varianzkollaps selbst.
Diese Analyse arbeitet deshalb mit den ganzen Vektoren, auf drei Ebenen:

1. Form der Vektoren   – Entropie, höchste Wahrscheinlichkeit, Anteil flacher / scharfer Vektoren,
                          Rundungsraster, Eingipfligkeit, Summe der Rohwerte
2. Differenzierung     – unterscheidet das Modell die Personen? (wiederholte Schablonen-Vektoren,
                          Abstand der Vektoren verschiedener Personen bei derselben Frage)
3. Populationsebene    – je Frage die Antwortverteilung der echten Personen gegen drei Lesarten des Modells:
                          (a) wahrscheinlichste Option, (b) Mittel der Vektoren, (c) gezogene Antwort

Eingabe: `antworten_LLM_detail.csv` eines Laufs und `ESS_fragebogen_DE.csv` (echte Antworten).
Ausgabe im Ergebnisordner des Laufs: `verteilungen_report.md`, `verteilungen_kennzahlen.csv`
und `verteilungen_items.csv`. Abbildungen entstehen nur in der Auswertung (analysis/forschungsfragen.py).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

K = np.arange(1, 7)
LOG2_6 = np.log2(6)

# Schwellen für die Einordnung eines Vektors
SHARP_MAXP = 0.8      # eine Option trägt mindestens 80 %
ONEHOT_MAXP = 0.99
FLAT_HNORM = 0.9      # normierte Entropie >= 0,9: nahe der Gleichverteilung

REPORT_MD = "verteilungen_report.md"
METRICS_CSV = "verteilungen_kennzahlen.csv"
ITEMS_CSV = "verteilungen_items.csv"


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def entropy_bits(P: np.ndarray) -> np.ndarray:
    P = np.asarray(P, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return -np.where(P > 0, P * np.log2(P), 0.0).sum(axis=-1)


def js_divergence(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Jensen-Shannon-Divergenz (Basis 2, zwischen 0 und 1) entlang der letzten Achse."""
    m = (p + q) / 2
    return entropy_bits(m) - (entropy_bits(p) + entropy_bits(q)) / 2


def wasserstein(p: np.ndarray, q: np.ndarray) -> float:
    """Wasserstein-1-Abstand zweier Verteilungen auf der geordneten Skala 1–6 (in Skalenpunkten)."""
    return float(np.abs(np.cumsum(p) - np.cumsum(q)).sum())


def histogram(values: np.ndarray) -> np.ndarray:
    v = np.asarray(values, float)
    v = v[(v >= 1) & (v <= 6)].astype(int)
    h = np.bincount(v, minlength=7)[1:].astype(float)
    return h / h.sum() if h.sum() else h


def dist_sd(p: np.ndarray) -> float:
    mu = p @ K
    return float(np.sqrt(max(p @ K**2 - mu**2, 0.0)))


def is_unimodal(p: np.ndarray, tol: float = 1e-9) -> bool:
    """Steigt bis zum Gipfel und fällt danach (Plateaus erlaubt)."""
    d = np.diff(p)
    sign = np.sign(np.where(np.abs(d) <= tol, 0, d))
    nz = sign[sign != 0]
    return not np.any((nz[:-1] < 0) & (nz[1:] > 0))


# ---------------------------------------------------------------------------
# Analyse eines Laufs
# ---------------------------------------------------------------------------

def load(run_dir: Path, human_csv: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    d = pd.read_csv(run_dir / "antworten_LLM_detail.csv")
    human = pd.read_csv(human_csv, dtype={"id": str}).set_index("id")
    return d, human


def analyse(run_dir: Path, human_csv: Path) -> tuple[dict, pd.DataFrame]:
    d, human = load(run_dir, human_csv)
    P = d[[f"p{i}" for i in K]].to_numpy(float)
    R = d[[f"p_roh{i}" for i in K]].to_numpy(float)
    n_persons = d["id"].nunique()

    H = entropy_bits(P)
    maxp = P.max(axis=1)
    top2 = np.sort(P, axis=1)[:, -2:].sum(axis=1)
    raw_sum = R.sum(axis=1)
    raw_vals = R.ravel()
    on_grid05 = np.isclose(raw_vals * 20, np.round(raw_vals * 20), atol=1e-6)
    on_grid10 = np.isclose(raw_vals * 10, np.round(raw_vals * 10), atol=1e-6)
    keys = [tuple(np.round(r, 4)) for r in R]
    vec_counts = pd.Series(keys).value_counts()

    # Abstand zwischen Personen: je Frage mittlere paarweise JS-Divergenz der Vektoren,
    # und wie viele Personen bei derselben Frage exakt denselben Vektor bekommen wie mindestens eine andere
    pair_js, shared, distinct_per_item = [], 0, []
    for _, g in d.groupby("item"):
        Q = g[[f"p{i}" for i in K]].to_numpy(float)
        iu = np.triu_indices(len(Q), 1)
        pair_js.append(js_divergence(Q[iu[0]], Q[iu[1]]).mean())
        c = pd.Series([tuple(np.round(r, 4)) for r in g[[f"p_roh{i}" for i in K]].to_numpy(float)]).value_counts()
        shared += int(c[c > 1].sum())
        distinct_per_item.append(len(c))

    # Populationsebene je Frage
    rows = []
    for item, g in d.groupby("item", sort=False):
        Q = g[[f"p{i}" for i in K]].to_numpy(float)
        h_vals = pd.to_numeric(human.loc[g["id"], item], errors="coerce").to_numpy()
        h = histogram(h_vals)
        mode = histogram(Q.argmax(axis=1) + 1)
        mix = Q.mean(axis=0)
        drawn = histogram(g["antwort_final"].to_numpy())
        exp = Q @ K
        rows.append({
            "frage": g["frage"].iloc[0], "item": item, "n_mensch": int(((h_vals >= 1) & (h_vals <= 6)).sum()),
            **{f"mensch_{k}": h[k - 1] for k in K}, **{f"mischung_{k}": mix[k - 1] for k in K},
            "js_modus": float(js_divergence(h, mode)), "js_mischung": float(js_divergence(h, mix)),
            "js_gezogen": float(js_divergence(h, drawn)),
            "w1_modus": wasserstein(h, mode), "w1_mischung": wasserstein(h, mix), "w1_gezogen": wasserstein(h, drawn),
            "sd_mensch": dist_sd(h), "sd_modus": dist_sd(mode), "sd_mischung": dist_sd(mix),
            "sd_gezogen": dist_sd(drawn),
            "sd_erwartung_zwischen_personen": float(exp.std(ddof=1)),
            "entropie_mittel": float(entropy_bits(Q).mean()),
        })
    items = pd.DataFrame(rows)

    m = {
        "lauf": run_dir.name, "personen": n_persons, "vektoren": len(P),
        "entropie_mittel_bit": H.mean(), "entropie_median_bit": float(np.median(H)),
        "entropie_p10_bit": float(np.percentile(H, 10)), "entropie_p90_bit": float(np.percentile(H, 90)),
        "entropie_norm_mittel": H.mean() / LOG2_6,
        "maxp_mittel": maxp.mean(), "top2_mittel": top2.mean(),
        "anteil_scharf": (maxp >= SHARP_MAXP).mean(), "anteil_onehot": (maxp >= ONEHOT_MAXP).mean(),
        "anteil_flach": (H / LOG2_6 >= FLAT_HNORM).mean(),
        "anteil_eingipflig": np.mean([is_unimodal(p) for p in P]),
        "sd_in_verteilung": float(np.mean([dist_sd(p) for p in P])),
        "anteil_raster_005": on_grid05.mean(), "anteil_raster_010": on_grid10.mean(),
        "rohsumme_abw_max": float(np.abs(raw_sum - 1).max()),
        "verschiedene_vektoren": len(vec_counts), "anteil_verschiedene_vektoren": len(vec_counts) / len(P),
        "haeufigster_vektor": " / ".join(f"{x:g}".replace(".", ",") for x in vec_counts.index[0]),
        "anteil_haeufigster_vektor": vec_counts.iloc[0] / len(P),
        "js_zwischen_personen": float(np.mean(pair_js)),
        "anteil_geteilt_gleiche_frage": shared / len(P),
        "verschiedene_vektoren_je_frage": float(np.mean(distinct_per_item)),
        **{k: items[k].mean() for k in ["js_modus", "js_mischung", "js_gezogen", "w1_modus", "w1_mischung",
                                         "w1_gezogen", "sd_mensch", "sd_modus", "sd_mischung", "sd_gezogen",
                                         "sd_erwartung_zwischen_personen"]},
    }
    return m, items


# ---------------------------------------------------------------------------
# Ausgabe
# ---------------------------------------------------------------------------

def _fmt(x: float, nd: int = 3) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _pct(x: float) -> str:
    return f"{100 * x:.1f} %".replace(".", ",")


def write_report(run_dir: Path, human_csv: Path) -> dict:
    m, items = analyse(run_dir, human_csv)
    pd.DataFrame([m]).to_csv(run_dir / METRICS_CSV, index=False)
    items.to_csv(run_dir / ITEMS_CSV, index=False)
    worst = items.sort_values("js_mischung", ascending=False).head(3)
    lines = [
        f"# Verteilungsanalyse: {m['lauf']}",
        "",
        f"{m['personen']} Personen × 21 Fragen = {m['vektoren']} Wahrscheinlichkeitsvektoren. "
        "Grundlage: `antworten_LLM_detail.csv` (p1–p6 normiert, p_roh1–p_roh6 wie vom Modell geliefert).",
        "",
        "## 1. Form der Vektoren",
        "",
        "| Kennzahl | Wert |",
        "|---|---|",
        f"| Entropie Mittel (Median; 10.–90. Perzentil) | {_fmt(m['entropie_mittel_bit'])} Bit "
        f"({_fmt(m['entropie_median_bit'])}; {_fmt(m['entropie_p10_bit'])}–{_fmt(m['entropie_p90_bit'])}) |",
        f"| Entropie relativ zur Gleichverteilung (2,585 Bit) | {_pct(m['entropie_norm_mittel'])} |",
        f"| höchste Wahrscheinlichkeit, Mittel | {_fmt(m['maxp_mittel'])} |",
        f"| Masse der zwei wahrscheinlichsten Optionen | {_fmt(m['top2_mittel'])} |",
        f"| Anteil scharfer Vektoren (max p ≥ {_fmt(SHARP_MAXP, 2)}) | {_pct(m['anteil_scharf'])} |",
        f"| Anteil One-Hot (max p ≥ {_fmt(ONEHOT_MAXP, 2)}) | {_pct(m['anteil_onehot'])} |",
        f"| Anteil flacher Vektoren (≥ {FLAT_HNORM * 100:.0f} % der Höchstentropie) | {_pct(m['anteil_flach'])} |",
        f"| Anteil eingipfliger Vektoren | {_pct(m['anteil_eingipflig'])} |",
        f"| SD innerhalb eines Vektors | {_fmt(m['sd_in_verteilung'])} Skalenpunkte |",
        f"| Rohwerte auf 0,05-Raster / 0,1-Raster | {_pct(m['anteil_raster_005'])} / {_pct(m['anteil_raster_010'])} |",
        f"| größte Abweichung der Rohsumme von 1 | {_fmt(m['rohsumme_abw_max'])} |",
        "",
        "## 2. Unterscheidet das Modell die Personen?",
        "",
        "| Kennzahl | Wert |",
        "|---|---|",
        f"| verschiedene Vektoren | {m['verschiedene_vektoren']} von {m['vektoren']} "
        f"({_pct(m['anteil_verschiedene_vektoren'])}) |",
        f"| häufigster Vektor | {m['haeufigster_vektor']} ({_pct(m['anteil_haeufigster_vektor'])} aller Vektoren) |",
        f"| verschiedene Vektoren je Frage (von {m['personen']} Personen, Mittel) | "
        f"{_fmt(m['verschiedene_vektoren_je_frage'], 1)} |",
        f"| Anteil Personen, die bei einer Frage denselben Vektor wie mindestens eine andere Person bekommen | "
        f"{_pct(m['anteil_geteilt_gleiche_frage'])} |",
        f"| JS-Divergenz zwischen Personen (gleiche Frage, Mittel) | {_fmt(m['js_zwischen_personen'])} |",
        f"| SD der Erwartungswerte zwischen Personen (je Frage, Mittel) | "
        f"{_fmt(m['sd_erwartung_zwischen_personen'])} |",
        "",
        "## 3. Populationsebene: echte Antwortverteilung je Frage gegen das Modell",
        "",
        "| Lesart des Modells | JS-Divergenz zum Menschen ↓ | Wasserstein-1 ↓ | SD der Antworten (Mensch "
        f"{_fmt(m['sd_mensch'])}) |",
        "|---|---|---|---|",
        f"| (a) nur wahrscheinlichste Option | {_fmt(m['js_modus'])} | {_fmt(m['w1_modus'])} | {_fmt(m['sd_modus'])} |",
        f"| (b) Mittel der vollen Vektoren | {_fmt(m['js_mischung'])} | {_fmt(m['w1_mischung'])} | "
        f"{_fmt(m['sd_mischung'])} |",
        f"| (c) gezogene Antwort (Pipeline) | {_fmt(m['js_gezogen'])} | {_fmt(m['w1_gezogen'])} | "
        f"{_fmt(m['sd_gezogen'])} |",
        "",
        "Fragen mit der größten Abweichung (Mittel der Vektoren gegen Mensch): "
        + ", ".join(f"{r.frage} `{r.item}` (JS {_fmt(r.js_mischung)})" for r in worst.itertuples()) + ".",
        "",
        f"Je Frage alle Werte: `{ITEMS_CSV}`.",
        "",
    ]
    (run_dir / REPORT_MD).write_text("\n".join(lines), encoding="utf-8")
    return m
