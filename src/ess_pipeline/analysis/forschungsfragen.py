"""
Auswertung entlang der Forschungsfragen (DOKUMENTATION.md, Abschnitt 5).

Je Unterfrage genau eine Abbildung; Titel, Dateiname und Übersicht im Report tragen dieselbe Nummer
(Zeichnen: forschungsfragen_plots.py):

    A1_beispielperson                eine Person und ihr Twin: Wahrscheinlichkeiten, Erwartungswert, Ziehung
    FF1a_genauigkeit                 MAE gegen Vergleichsgrößen ohne Personenwissen
    FF1b_profil                      Spearman ρ: ganzes Profil und individuelle Abweichung
    A3_fehler_je_twin                Verteilung von MAE und ρ je Twin
    FF1b2_trennschaerfe              (1b′) Korrelation über Personen je Frage
    FF1c_bias                        Mean Error je Frage mit 95-%-KI
    FF1d_subgruppen                  MAE je Gruppe (inkl. Werte-Milieu)
    FF1e_varianzkollaps              Within-Cell-SD Person vs. Twin (gezogen und Erwartungswert)
    A2_varianzzerlegung              Varianz der Twins: zwischen Erwartungswerten + durch die Ziehung
    FF2_0_milieus_existenz           Silhouette je k gegen Zufallsdaten ohne Gruppen
    FF2_1_milieus                    Milieus im Wertekreis
    FF2a_lage                        Werteprofile der Milieu-Mittelpunkte
    FF2b_streuung                    tr(Σ) Person vs. Twin (gezogen und Erwartungswert), Bures-Wasserstein
    FF2c_form                        Verteilung je Wert
    FF2d_zuordnung                   Kreuztabelle Milieu Person × Milieu Twin
    Fazit3_werte_oder_demografie     R² der Demografie je Wert, Person vs. Twin

Tests, Konfidenzintervalle, Regression und Konfusionsmatrix stehen in den CSV-Dateien und im Report.

Aufruf:  python run_llm.py --stages auswertung   (Lauf aus config/llm_experiment.yaml)
         python -m ess_pipeline.analysis.forschungsfragen results/llm/<lauf>
Ausgabe: results/auswertung/<lauf>/ (report.md, kennzahlen.csv, twins.csv, … und figures/)
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.mixture import GaussianMixture

from ..config import ESS_ITEM_MAP, ID_COL, PVQ_ITEMS, Paths
from . import ebene1, ebene2
from . import forschungsfragen_plots as P
from .data import BASIC_VALUES, ITEM_VALUE, SUBGROUPS, Twins, load_twins
from .ebene1 import _group_order

K = 2                    # fest, siehe 2.0: Silhouette der Menschen am höchsten bei k = 2
N_BOOT = 1000
N_PERM = 500
CELL = ["Geschlecht", "Alter", "Schulabschluss"]   # Demografie-Zellen für Zellmittel und Varianzkollaps
MIN_CELL_N = 20


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def _de(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def _pval(p: float) -> str:
    return "p < 0,001" if p < 0.001 else f"p = {_de(p, 3)}"












def _ci_mean(x: np.ndarray) -> tuple[float, float]:
    m, lo, hi = ebene1.mean_ci(x)
    return m, (hi - lo) / 2


# ---------------------------------------------------------------------------
# Ebene 1 – zusätzliche Vergleichsgrößen
# ---------------------------------------------------------------------------

def cell_labels(t: Twins) -> pd.Series:
    d = t.demo[CELL]
    lab = d.astype(str).agg(" · ".join, axis=1)
    return lab.where(d.notna().all(axis=1))


def cell_mean_profile(t: Twins) -> np.ndarray:
    """Demografie-Zellmittel, leave-one-out: mittlere Antwort der *anderen* Menschen derselben Zelle."""
    h = t.items("human")
    pop = h.mean(axis=0)
    out = np.tile(pop, (len(h), 1))
    lab = cell_labels(t).to_numpy()
    for c in pd.unique(lab[pd.notna(lab)]):
        idx = np.flatnonzero(lab == c)
        if len(idx) < 2:
            continue
        s = h[idx].sum(axis=0)
        out[idx] = (s - h[idx]) / (len(idx) - 1)
    return np.round(out, 9)   # exakte Bindungen für Rangkorrelationen


def uniform_mae(h: np.ndarray) -> np.ndarray:
    """Erwarteter MAE je Person, wenn jede Antwort gleichverteilt aus 1–6 gezogen wird (exakt, ohne Ziehung)."""
    k = np.arange(1, 7)
    return np.abs(h[..., None] - k).mean(axis=-1).mean(axis=1)


def deviation_spearman(h: np.ndarray, lm: np.ndarray) -> np.ndarray:
    """ρ zwischen den Abweichungen vom jeweiligen Populationsmittel je Item: der personenspezifische Anteil."""
    return ebene1.rowwise_spearman(h - h.mean(axis=0), lm - lm.mean(axis=0))


def expected_answers(run_dir: Path, t: Twins) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Aus den Wahrscheinlichkeitsvektoren p1 … p6 (antworten_LLM_detail.csv), umgepolt wie die Items (6 = sehr wichtig):
    Erwartungswert Σ k·pk, Varianz innerhalb des Vektors und die Vektoren selbst (Index 0 = Antwort 1 nach Umpolung).
    Form (Personen, Items) bzw. (Personen, Items, 6), Reihenfolge wie t.ids und PVQ_ITEMS.
    """
    d = pd.read_csv(run_dir / "antworten_LLM_detail.csv", dtype={ID_COL: str})
    d = d.drop_duplicates([ID_COL, "item"], keep="last").set_index([ID_COL, "item"])
    idx = pd.MultiIndex.from_product([t.ids, PVQ_ITEMS])
    p = d[[f"p{k}" for k in range(1, 7)]].reindex(idx).to_numpy(float)[:, ::-1]   # umpolen: Rohantwort k -> 7 − k
    p = p / p.sum(axis=1, keepdims=True)
    k = np.arange(1, 7)
    e = np.round(p @ k, 9)   # gerundet, damit gleiche Erwartungswerte in Rangkorrelationen exakt gebunden sind
    var = p @ k**2 - (p @ k) ** 2
    shape = (len(t.ids), len(PVQ_ITEMS))
    return e.reshape(shape), var.reshape(shape), p.reshape(*shape, 6)


def _colwise_spearman(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Spearman ρ je Spalte (Item) über die Zeilen (Personen); Bindungen gemittelt wie scipy.stats.spearmanr."""
    ra, rb = stats.rankdata(a, axis=0), stats.rankdata(b, axis=0)
    ra, rb = ra - ra.mean(0), rb - rb.mean(0)
    return (ra * rb).sum(0) / np.sqrt((ra**2).sum(0) * (rb**2).sum(0))


def item_spearman_boot(h: np.ndarray, le: np.ndarray, cellp: np.ndarray, rng: np.random.Generator,
                       reps: int = N_BOOT) -> tuple[np.ndarray, np.ndarray]:
    """
    1b′: paarweiser Bootstrap über Personen (dieselbe Stichprobe für Twin und Demografie-Mittelwert).
    Rückgabe: 95-%-Intervall von ρ Twin je Item und von ρ Twin − ρ Demografie-Mittelwert, je Form (2, Items).
    """
    tw, diff = [], []
    for _ in range(reps):
        i = rng.integers(0, len(h), len(h))
        a = _colwise_spearman(h[i], le[i])
        tw.append(a)
        diff.append(a - _colwise_spearman(h[i], cellp[i]))
    return np.quantile(tw, [0.025, 0.975], axis=0), np.quantile(diff, [0.025, 0.975], axis=0)


def redraw(p: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Neue Ziehung aus den Wahrscheinlichkeitsvektoren (Personen, Items, 6): eine Antwort 1–6 je Feld."""
    u = rng.random(p.shape[:2] + (1,))
    return np.minimum((p.cumsum(axis=-1) < u).sum(axis=-1) + 1, 6)


def value_scores(x: np.ndarray) -> np.ndarray:
    """Zentrierte Basiswerte wie scoring.compute_scores, aber auch für nicht ganzzahlige Antworten (Erwartungswerte)."""
    col = {item: j for j, item in enumerate(PVQ_ITEMS)}
    mrat = x.mean(axis=1, keepdims=True)
    return np.column_stack([x[:, [col[i] for i in ESS_ITEM_MAP[v]]].mean(axis=1) for v in BASIC_VALUES]) - mrat


def varianzzerlegung(h: np.ndarray, le: np.ndarray, lvar: np.ndarray) -> pd.DataFrame:
    """
    Satz von der totalen Varianz je Item: Varianz der gezogenen Antworten ≈ Varianz der Erwartungswerte zwischen den
    Twins + mittlere Varianz innerhalb eines Vektors (Zufall der Ziehung). Dazu die Varianz der echten Antworten.
    """
    df = pd.DataFrame({"item": PVQ_ITEMS, "wert": [ITEM_VALUE[i] for i in PVQ_ITEMS],
                       "var_mensch": h.var(axis=0), "var_zwischen": le.var(axis=0), "var_ziehung": lvar.mean(axis=0)})
    df["var_twin_gesamt"] = df["var_zwischen"] + df["var_ziehung"]
    df["anteil_zwischen"] = df["var_zwischen"] / df["var_twin_gesamt"]
    return df


def milieu_names(centroids: np.ndarray) -> list[str]:
    """'Milieu c (offen)' für das Milieu mit der höheren Offenheit − Bewahrung, das andere '(bewahrend)' (k = 2)."""
    v = {b: j for j, b in enumerate(BASIC_VALUES)}
    y = centroids[:, [v["SD"], v["ST"], v["HE"]]].mean(1) - centroids[:, [v["SE"], v["CO"], v["TR"]]].mean(1)
    return [f"Milieu {c + 1} ({'offen' if y[c] == y.max() else 'bewahrend'})" for c in range(len(centroids))]


def per_person_shuffle(h: np.ndarray, lm: np.ndarray, rng: np.random.Generator, reps: int = 20,
                       deviation: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """MAE und ρ gegen fremde LLM-Antworten, je Person gemittelt über `reps` Zufallspaarungen."""
    mae, rho = [], []
    for _ in range(reps):
        ls = ebene1._shuffled(lm, rng)
        mae.append(np.abs(ls - h).mean(axis=1))
        rho.append(deviation_spearman(h, ls) if deviation else ebene1.rowwise_spearman(h, ls))
    return np.mean(mae, axis=0), np.nanmean(rho, axis=0)


def ebene1_kern(t: Twins, x: np.ndarray, cellp: np.ndarray, demo: pd.DataFrame, seed: int,
                boot: bool = True) -> dict:
    """
    Kernkennzahlen der Ebene 1 für eine Twin-Matrix x (Erwartungswerte oder gezogene Antworten), mit derselben
    Rechnung für beide Varianten (Sensitivitätsanalyse, DOKUMENTATION.md 5.6). Vergleichsgrößen unverändert.
    Die Zufallsgeneratoren sind wie im Hauptablauf gesetzt (Seed für die Zufallspaarung, seed + 2 für den
    Bootstrap), damit die Variante mit Erwartungswerten exakt die Zahlen des Berichts ergibt.
    """
    h = t.items("human")
    rng = np.random.default_rng(seed)
    shuf_mae, _ = per_person_shuffle(h, x, rng)
    _, shuf_dev = per_person_shuffle(h, x, rng, deviation=True)
    e = x - h
    mae = np.abs(e).mean(axis=1)
    mae_cell = np.abs(cellp - h).mean(axis=1)
    dev, dev_cell = deviation_spearman(h, x), deviation_spearman(h, cellp)
    rho_item = _colwise_spearman(h, x)
    rho_item_cell = _colwise_spearman(h, cellp)
    p_item = stats.ttest_1samp(e, 0).pvalue
    sig = ebene1.holm(p_item) < 0.05
    dz = (x - x.mean(axis=1, keepdims=True)) - (h - h.mean(axis=1, keepdims=True))
    sub = subgroup_stats(pd.DataFrame({"mae": mae}), demo)["tests"]
    X = demo_design(t)
    ok = X.notna().all(axis=1).to_numpy()
    k = {
        ("1a", "MAE Twin"): mae.mean(),
        ("1a", "MAE fremder Twin"): shuf_mae.mean(),
        ("1a", "MAE Demografie-Mittelwert"): mae_cell.mean(),
        ("1a", "RMSE Twin"): np.sqrt((e**2).mean(axis=1)).mean(),
        ("1a", "Anteil Twins genauer als fremder Twin"): float((mae < shuf_mae).mean()),
        ("A3", "Anteil Twins genauer als Demografie-Mittelwert (MAE)"): float((mae < mae_cell).mean()),
        ("1b", "ρ Profil Twin (Mittel)"): np.nanmean(ebene1.rowwise_spearman(h, x)),
        ("1b", "ρ individuelle Abweichung Twin (Mittel)"): np.nanmean(dev),
        ("1b", "ρ individuelle Abweichung fremder Twin (Mittel)"): np.nanmean(shuf_dev),
        ("1b", "ρ individuelle Abweichung Demografie-Mittelwert (Mittel)"): np.nanmean(dev_cell),
        ("1b", "Differenz ρ individuelle Abweichung Twin − Demografie-Mittelwert"): np.nanmean(dev - dev_cell),
        ("1b", "Wilcoxon individuelle Abweichung Twin vs. Demografie-Mittelwert p"):
            stats.wilcoxon(dev, dev_cell, nan_policy="omit").pvalue,
        ("A3", "Anteil Twins mit ρ individuelle Abweichung > Demografie-Mittelwert"): float((dev > dev_cell).mean()),
        ("1b′", "ρ je Frage Twin (Mittel)"): rho_item.mean(),
        ("1b′", "ρ je Frage Demografie-Mittelwert (Mittel)"): rho_item_cell.mean(),
        ("1b′", "Fragen mit ρ Twin > Demografie-Mittelwert"): int((rho_item > rho_item_cell).sum()),
        ("1c", "ME gesamt"): e.mean(),
        ("1c", "Fragen mit gerichtetem Fehler (Holm)"): int(sig.sum()),
        ("1c", "davon unterschätzt"): int((sig & (e.mean(axis=0) < 0)).sum()),
        ("1c", "Fragen mit gerichtetem Fehler nach Zentrierung (Holm)"):
            int((ebene1.holm(stats.ttest_1samp(dz, 0).pvalue) < 0.05).sum()),
        ("1d", "η² Schulabschluss"): float(sub.set_index("merkmal").loc["Schulabschluss", "eta2"]),
        ("1d", "Merkmale mit signifikantem MAE-Unterschied (Holm)"): int((sub.p_holm < 0.05).sum()),
        ("1d", "Regression MAE ~ Demografie R²"): ols(mae[ok], X[ok])[1],
    }
    if boot:
        _, ci_diff = item_spearman_boot(h, x, cellp, np.random.default_rng(seed + 2))
        k[("1b′", "Fragen gesichert besser als Demografie-Mittelwert (Bootstrap)")] = int((ci_diff[0] > 0).sum())
        k[("1b′", "Fragen gesichert schlechter als Demografie-Mittelwert (Bootstrap)")] = int((ci_diff[1] < 0).sum())
    return k


# Aussagen, deren Gültigkeit je Variante geprüft wird: (Unterfrage, Aussage, Prüfung auf ebene1_kern)
AUSSAGEN = [
    ("1a", "Twin genauer als fremder Twin (MAE)", lambda k: k[("1a", "MAE Twin")] < k[("1a", "MAE fremder Twin")]),
    ("1a", "Twin genauer als Demografie-Mittelwert (MAE)",
     lambda k: k[("1a", "MAE Twin")] < k[("1a", "MAE Demografie-Mittelwert")]),
    ("A3", "Mehrheit der Twins genauer als ihr Demografie-Mittelwert (MAE)",
     lambda k: k[("A3", "Anteil Twins genauer als Demografie-Mittelwert (MAE)")] > 0.5),
    ("1b", "Twin enthält Information über die Person (individuelle Abweichung über fremdem Twin)",
     lambda k: k[("1b", "ρ individuelle Abweichung Twin (Mittel)")]
     > k[("1b", "ρ individuelle Abweichung fremder Twin (Mittel)")]),
    ("1b", "Twin trifft die individuelle Abweichung mindestens so gut wie der Demografie-Mittelwert",
     lambda k: k[("1b", "Differenz ρ individuelle Abweichung Twin − Demografie-Mittelwert")] >= 0),
    ("A3", "Mehrheit der Twins trifft die individuelle Abweichung besser als ihr Demografie-Mittelwert",
     lambda k: k[("A3", "Anteil Twins mit ρ individuelle Abweichung > Demografie-Mittelwert")] > 0.5),
    ("1b′", "Twin trennt die Personen bei der Mehrheit der Fragen besser als der Demografie-Mittelwert",
     lambda k: k[("1b′", "Fragen mit ρ Twin > Demografie-Mittelwert")] > len(PVQ_ITEMS) / 2),
    ("1c", "Fehler bei der Mehrheit der Fragen gerichtet, überwiegend nach unten",
     lambda k: k[("1c", "Fragen mit gerichtetem Fehler (Holm)")] > len(PVQ_ITEMS) / 2
     and k[("1c", "davon unterschätzt")] > k[("1c", "Fragen mit gerichtetem Fehler (Holm)")] / 2),
    ("1d", "Schulabschluss hängt spürbar mit dem MAE zusammen (η² ≥ 0,01)",
     lambda k: k[("1d", "η² Schulabschluss")] >= 0.01),
]


def sensitivitaet_ebene1(t: Twins, le: np.ndarray, lm: np.ndarray, redraws: list[np.ndarray], cellp: np.ndarray,
                         demo: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Ebene 1 vollständig mit gezogenen Antworten statt Erwartungswerten (Sensitivitätsanalyse).
    Rückgabe: (kennzahlen, aussagen). `redraws` = neue Ziehungen aus denselben Wahrscheinlichkeitsvektoren; sie
    zeigen, ob ein Unterschied an der Wahl Erwartungswert/Ziehung liegt oder nur an der einen Ziehung des Laufs.
    """
    k_e = ebene1_kern(t, le, cellp, demo, seed)
    k_g = ebene1_kern(t, lm, cellp, demo, seed)
    k_r = [ebene1_kern(t, d, cellp, demo, seed, boot=False) for d in redraws]
    rows = []
    for key in k_e:
        r = [kr[key] for kr in k_r if key in kr]
        rows.append({"unterfrage": key[0], "kennzahl": key[1], "erwartungswert": k_e[key], "gezogen": k_g[key],
                     "neuziehungen_min": min(r) if r else np.nan, "neuziehungen_max": max(r) if r else np.nan})
    aus = []
    for uf, text, test in AUSSAGEN:
        e_, g_ = bool(test(k_e)), bool(test(k_g))
        anteil = float(np.mean([test(kr) for kr in k_r]))
        aus.append({"unterfrage": uf, "aussage": text, "erwartungswert": e_, "gezogen": g_,
                    "gezogen_anteil_neuziehungen": anteil, "haengt_von_wahl_ab": e_ != g_})
    return pd.DataFrame(rows), pd.DataFrame(aus)


def ols(y: np.ndarray, X: pd.DataFrame) -> tuple[pd.DataFrame, float, float, float]:
    """OLS mit Konstante. Rückgabe: Koeffiziententabelle (ohne Konstante), R², F, p(F)."""
    Xm = np.column_stack([np.ones(len(X)), X.to_numpy(float)])
    beta, *_ = np.linalg.lstsq(Xm, y, rcond=None)
    resid = y - Xm @ beta
    n, p = Xm.shape
    s2 = resid @ resid / (n - p)
    se = np.sqrt(np.diag(s2 * np.linalg.pinv(Xm.T @ Xm)))
    tval = beta / se
    pv = 2 * stats.t.sf(np.abs(tval), n - p)
    q = stats.t.ppf(0.975, n - p)
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    f = (r2 / (p - 1)) / ((1 - r2) / (n - p))
    coef = pd.DataFrame({"term": X.columns, "b": beta[1:], "se": se[1:], "ci_unten": beta[1:] - q * se[1:],
                         "ci_oben": beta[1:] + q * se[1:], "p": pv[1:]})
    return coef, float(r2), float(f), float(stats.f.sf(f, p - 1, n - p))


def demo_design(t: Twins) -> pd.DataFrame:
    """Dummy-Kodierung aller Subgruppen-Merkmale; Referenz = erste Kategorie in natürlicher Reihenfolge."""
    parts = []
    for var in SUBGROUPS:
        lab = t.demo[var]
        order = _group_order(lab)
        for g in order[1:]:
            parts.append(pd.Series((lab == g).astype(float).where(lab.notna()), name=f"{var}: {g}"))
    return pd.concat(parts, axis=1)




def varianzkollaps(t: Twins, rng: np.random.Generator, le: np.ndarray | None = None) -> pd.DataFrame:
    """
    Je Item: mittlere Within-Cell-SD (Zellen Geschlecht × Alter × Bildung, n ≥ MIN_CELL_N) für Menschen
    und LLM-Twins, plus Bootstrap-Referenz der menschlichen SD (je Zelle mit Zurücklegen, gleiches N).
    `le` = Erwartungswerte der Twins; dann zusätzlich deren Within-Cell-SD (sd_llm_erwartung).
    """
    h, lm = t.items("human"), t.items("llm")
    lab = cell_labels(t).to_numpy()
    cells = [np.flatnonzero(lab == c) for c in pd.unique(lab[pd.notna(lab)])]
    cells = [c for c in cells if len(c) >= MIN_CELL_N]
    w = np.array([len(c) for c in cells], float)
    w /= w.sum()
    sd_h = np.array([h[c].std(axis=0, ddof=1) for c in cells])        # (Zellen, Items)
    sd_l = np.array([lm[c].std(axis=0, ddof=1) for c in cells])
    boot = np.zeros((N_BOOT, h.shape[1]))
    for ci, c in enumerate(cells):
        idx = c[rng.integers(0, len(c), (N_BOOT, len(c)))]             # (B, n_c)
        boot += w[ci] * h[idx].std(axis=1, ddof=1)                      # (B, Items)
    df = pd.DataFrame({
        "item": PVQ_ITEMS, "wert": [ITEM_VALUE[i] for i in PVQ_ITEMS],
        "sd_mensch": w @ sd_h, "sd_llm": w @ sd_l,
        "boot_unten": np.quantile(boot, 0.025, axis=0), "boot_oben": np.quantile(boot, 0.975, axis=0),
        "anteil_zellen_llm_kleiner": (sd_l < sd_h).mean(axis=0),
    })
    df["verhaeltnis"] = df["sd_llm"] / df["sd_mensch"]
    if le is not None:
        df["sd_llm_erwartung"] = w @ np.array([le[c].std(axis=0, ddof=1) for c in cells])
    df.attrs["n_zellen"] = len(cells)
    df.attrs["n_personen"] = int(sum(len(c) for c in cells))
    return df


# ---------------------------------------------------------------------------
# Ebene 2 – LPA, Matching, Kennzahlen
# ---------------------------------------------------------------------------

def lpa(x: np.ndarray, k: int, seed: int) -> GaussianMixture:
    """Latent Profile Analysis = Gauß-Mischung mit diagonaler Kovarianz (lokale Unabhängigkeit)."""
    return GaussianMixture(k, covariance_type="diag", n_init=20, random_state=seed).fit(x)


def matched(ch: np.ndarray, cl: np.ndarray) -> np.ndarray:
    """inv[j] = menschliches Milieu, das LLM-Milieu j zugeordnet wird (Hungarian auf Zentroid-Abständen)."""
    cost = np.linalg.norm(ch[:, None] - cl[None], axis=2)
    r, c = linear_sum_assignment(cost)
    inv = np.empty(len(ch), int)
    inv[c] = r
    return inv


def jaccard(a: np.ndarray, b: np.ndarray, k: int) -> np.ndarray:
    return np.array([np.sum((a == c) & (b == c)) / max(np.sum((a == c) | (b == c)), 1) for c in range(k)])


def jaccard_chance(a: np.ndarray, b: np.ndarray, k: int, rng: np.random.Generator, reps: int = 200) -> np.ndarray:
    return np.mean([jaccard(a, rng.permutation(b), k) for _ in range(reps)], axis=0)


def mmd_null(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, n_perm: int = N_PERM):
    """MMD² (RBF, Median-Heuristik) und seine Permutations-Nullverteilung."""
    z = np.vstack([x, y])
    n, m = len(x), len(y)
    d2 = ebene2._sq_dists(z)
    sigma = float(np.sqrt(np.median(d2[np.triu_indices(len(z), 1)])))
    kmat = np.exp(-d2 / (2 * sigma**2)).astype(np.float32)
    del d2

    def stat(u):
        v = 1 - u
        ku, kv = kmat @ u, kmat @ v
        return (((u * ku).sum(0) - n) / (n * (n - 1)) + ((v * kv).sum(0) - m) / (m * (m - 1))
                - 2 * (u * kv).sum(0) / (n * m))

    obs = np.zeros((n + m, 1), np.float32)
    obs[:n] = 1
    perms = np.zeros((n + m, n_perm), np.float32)
    for j in range(n_perm):
        perms[rng.permutation(n + m)[:n], j] = 1
    o, null = float(stat(obs)[0]), stat(perms)
    return o, null, float((1 + np.sum(null >= o)) / (1 + n_perm))


def gaussian_null_silhouette(x: np.ndarray, ks, seed: int, reps: int = 5) -> pd.DataFrame:
    """Silhouette von k-Means auf einer Normalverteilung mit gleicher Kovarianz: so sieht 'keine Cluster' aus."""
    rng = np.random.default_rng(seed)
    cov, mu = np.cov(x, rowvar=False), x.mean(axis=0)
    rows = []
    for r in range(reps):
        z = rng.multivariate_normal(mu, cov, len(x), check_valid="ignore")
        for k in ks:
            lab = KMeans(k, n_init=10, random_state=seed + r).fit_predict(z)
            rows.append({"k": k, "rep": r, "silhouette": silhouette_score(z, lab)})
    return pd.DataFrame(rows).groupby("k")["silhouette"].agg(["mean", "min", "max"]).reset_index()


# ---------------------------------------------------------------------------
# Hauptablauf
# ---------------------------------------------------------------------------

def run(run_dir: Path, seed: int = 42, paths: Paths | None = None) -> Path:
    paths = paths or Paths()
    out = paths.analysis_dir / run_dir.name
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    for old_png in fig_dir.glob("*.png"):   # nur erzeugte Abbildungen, damit keine veralteten liegen bleiben
        old_png.unlink()
    rng = np.random.default_rng(seed)
    t = load_twins(run_dir, paths.questionnaire_csv, paths.scores_csv, paths.profile_csv)
    h, lm = t.items("human"), t.items("llm")   # lm = gezogene Antworten
    le, lvar, lp = expected_answers(run_dir, t)
    # Datengrundlage: Ebene 1 rechnet mit Erwartungswerten. Mittelwert und Demografie-Mittelwert sind selbst
    # Erwartungswerte; gegen die gezogene Antwort trüge nur der Twin das Rauschen der Ziehung, das per Konstruktion
    # nichts über die Person weiß. Ebene 2 rechnet mit gezogenen Antworten (die synthetische Stichprobe als Datensatz).
    te = replace(t, llm=pd.DataFrame(le, index=t.llm.index, columns=t.llm.columns))
    rng_neu = np.random.default_rng(seed + 1)   # eigene Ziehungen für neue Größen: bisherige Kennzahlen bleiben gleich
    n = len(t.ids)
    K_ = []  # Kennzahlen (Unterfrage, Kennzahl, Wert)

    def kz(uf, name, val, vergleich=""):
        K_.append({"unterfrage": uf, "kennzahl": name, "wert": val, "vergleich": vergleich})

    # ===================== Ebene 1 (Erwartungswerte) =====================
    twins = ebene1.twin_table(te)
    base = ebene1.baselines(te, seed)
    items = ebene1.item_table(te, base)
    # exakte Treffer gibt es nur bei ganzzahligen, also gezogenen Antworten
    twins["exakt"] = (lm == h).mean(axis=1)
    items["exakt"] = (lm == h).mean(axis=0)[[PVQ_ITEMS.index(i) for i in items["item"]]]

    cellp = cell_mean_profile(t)
    popp = np.broadcast_to(t.population_mean, h.shape)
    shuf_mae, shuf_rho = per_person_shuffle(h, le, rng)
    _, shuf_dev_rho = per_person_shuffle(h, le, rng, deviation=True)
    twins["mae_zufallspaarung"] = shuf_mae
    twins["mae_zellmittel"] = np.abs(cellp - h).mean(axis=1)
    twins["mae_mittelprofil"] = np.abs(popp - h).mean(axis=1)
    twins["mae_zufall_1_6"] = uniform_mae(h)
    twins["spearman_zufallspaarung"] = shuf_rho
    twins["spearman_zellmittel"] = ebene1.rowwise_spearman(h, cellp)
    twins["spearman_mittelprofil"] = ebene1.rowwise_spearman(h, popp)
    twins["spearman_abweichung"] = deviation_spearman(h, le)
    twins["spearman_abweichung_zufallspaarung"] = shuf_dev_rho
    twins["spearman_abweichung_zellmittel"] = deviation_spearman(h, cellp)
    twins["mae_zufallspaarung_einzeln"] = np.abs(ebene1._shuffled(le, rng_neu) - h).mean(axis=1)
    twins["spearman_abweichung_zufallspaarung_einzeln"] = deviation_spearman(h, ebene1._shuffled(le, rng_neu))
    # zum Vergleich: dieselben Größen mit gezogenen Antworten
    twins["mae_gezogen"] = np.abs(lm - h).mean(axis=1)
    twins["spearman_gezogen"] = ebene1.rowwise_spearman(h, lm)
    twins["spearman_abweichung_gezogen"] = deviation_spearman(h, lm)
    items["spearman_item_gezogen"] = [stats.spearmanr(h[:, PVQ_ITEMS.index(i)], lm[:, PVQ_ITEMS.index(i)]).statistic
                                      for i in items["item"]]

    mae_src = {
        "Zufall 1–6": twins["mae_zufall_1_6"], "Zufallspaarung\n(fremder Twin)": twins["mae_zufallspaarung"],
        "LLM-Twin": twins["mae"], "Demografie-\nZellmittel": twins["mae_zellmittel"],
        "Mittelprofil\n(ESS-Durchschnitt)": twins["mae_mittelprofil"],
    }
    for k_, v in mae_src.items():
        kz("1a", f"MAE {k_.replace('-' + chr(10), '-').replace(chr(10), ' ')}", v.mean())
    kz("1a", "RMSE LLM-Twin", twins["rmse"].mean(), f"Zufallspaarung {base['shuffle_rmse']:.3f}, "
                                                    f"Mittelprofil {base['mittelprofil_rmse']:.3f}")
    kz("1a", "Anteil exakter Treffer (gezogen)", twins["exakt"].mean())
    kz("1a", "MAE Twin gezogen", twins["mae_gezogen"].mean())
    better = {k_: float((twins["mae"] < twins[c]).mean()) for k_, c in
              [("Zufall 1–6", "mae_zufall_1_6"), ("Zufallspaarung", "mae_zufallspaarung"),
               ("Demografie-Zellmittel", "mae_zellmittel"), ("Mittelprofil", "mae_mittelprofil")]}
    for k_, v in better.items():
        kz("1a", f"Anteil Twins genauer als {k_}", v)
    w = stats.wilcoxon(twins["mae"], twins["mae_zufallspaarung"])
    kz("1a", "Wilcoxon Twin vs. Zufallspaarung p", w.pvalue)

    for c, name in [("spearman", "LLM-Twin"), ("spearman_zufallspaarung", "Zufallspaarung"),
                    ("spearman_zellmittel", "Zellmittel"), ("spearman_mittelprofil", "Mittelprofil")]:
        kz("1b", f"ρ Profil {name} (Mittel)", twins[c].mean())
    kz("1b", "Anteil ρ > 0 LLM-Twin", float((twins["spearman"] > 0).mean()))
    kz("1b", "Anteil ρ undefiniert", float(twins["spearman"].isna().mean()))
    for c, name in [("spearman_abweichung", "LLM-Twin"), ("spearman_abweichung_zufallspaarung", "Zufallspaarung"),
                    ("spearman_abweichung_zellmittel", "Zellmittel")]:
        kz("1b", f"ρ Abweichungsprofil {name} (Mittel)", twins[c].mean())
    kz("1b", "Anteil ρ Abweichungsprofil > 0", float((twins["spearman_abweichung"] > 0).mean()))
    w = stats.wilcoxon(twins["spearman_abweichung"], twins["spearman_abweichung_zufallspaarung"], nan_policy="omit")
    kz("1b", "Wilcoxon Abweichungs-ρ Twin vs. Zufallspaarung p", w.pvalue)
    kz("1b", "Anteil Twins mit Abweichungs-ρ > Zellmittel",
       float((twins["spearman_abweichung"] > twins["spearman_abweichung_zellmittel"]).mean()))
    w = stats.wilcoxon(twins["spearman_abweichung"], twins["spearman_abweichung_zellmittel"], nan_policy="omit")
    kz("1b", "Wilcoxon Abweichungs-ρ Twin vs. Zellmittel p", w.pvalue)
    kz("1b", "ρ Profil LLM-Twin gezogen (Mittel)", twins["spearman_gezogen"].mean())
    kz("1b", "ρ Abweichungsprofil LLM-Twin gezogen (Mittel)", twins["spearman_abweichung_gezogen"].mean())

    # items ist nach Fragebogen sortiert, cellp nach PVQ_ITEMS
    items["spearman_item_zellmittel"] = [stats.spearmanr(h[:, PVQ_ITEMS.index(i)], cellp[:, PVQ_ITEMS.index(i)]).statistic
                                         for i in items["item"]]
    j_items = [PVQ_ITEMS.index(i) for i in items["item"]]
    ci_tw, ci_diff = item_spearman_boot(h, le, cellp, np.random.default_rng(seed + 2))
    items["spearman_item_ci_unten"], items["spearman_item_ci_oben"] = ci_tw[0, j_items], ci_tw[1, j_items]
    items["diff_zellmittel_ci_unten"], items["diff_zellmittel_ci_oben"] = ci_diff[0, j_items], ci_diff[1, j_items]
    items["besser_als_zellmittel_gesichert"] = items["diff_zellmittel_ci_unten"] > 0
    items["schlechter_als_zellmittel_gesichert"] = items["diff_zellmittel_ci_oben"] < 0
    kz("1b′", "Items gesichert besser als Zellmittel (Bootstrap-KI der Differenz > 0)",
       int(items["besser_als_zellmittel_gesichert"].sum()))
    kz("1b′", "Items gesichert schlechter als Zellmittel", int(items["schlechter_als_zellmittel_gesichert"].sum()))
    kz("1b′", "spearman_item Mittel LLM", items["spearman_item"].mean())
    kz("1b′", "spearman_item Mittel LLM gezogen", items["spearman_item_gezogen"].mean())
    kz("1b′", "spearman_item Mittel Zellmittel", items["spearman_item_zellmittel"].mean())
    kz("1b′", "Items mit LLM-ρ > Zellmittel-ρ", int((items["spearman_item"] > items["spearman_item_zellmittel"]).sum()))
    kz("1b′", "Items mit LLM-ρ gezogen > Zellmittel-ρ",
       int((items["spearman_item_gezogen"] > items["spearman_item_zellmittel"]).sum()))

    kz("1c", "ME gesamt", twins["me"].mean())
    kz("1c", "Items mit signifikantem Bias (Holm)", int(items["signifikant"].sum()))
    kz("1c", "davon unterschätzt", int((items["signifikant"] & (items["me"] < 0)).sum()))
    # Robustheit: Mean Error nach Zentrierung je Person (persönlicher Mittelwert über 21 Fragen abgezogen, wie in
    # Ebene 2). Trennt den Antwortstil (Twin antwortet insgesamt niedriger) von der Gewichtung einzelner Werte.
    dz = (le - le.mean(axis=1, keepdims=True)) - (h - h.mean(axis=1, keepdims=True))
    items["me_zentriert"] = dz.mean(axis=0)[j_items]
    items["p_zentriert_holm"] = ebene1.holm(stats.ttest_1samp(dz, 0).pvalue[j_items])
    items["signifikant_zentriert"] = items["p_zentriert_holm"] < 0.05
    kz("1c", "Items mit signifikantem Bias nach Zentrierung (Holm)", int(items["signifikant_zentriert"].sum()))
    kz("1c", "Items mit gleicher Richtung roh und zentriert (beide signifikant)",
       int((items.signifikant & items.signifikant_zentriert & (np.sign(items.me) == np.sign(items.me_zentriert))).sum()))

    # ===================== Ebene 2 =====================
    xh = t.human_scores[BASIC_VALUES].to_numpy(float)
    xl = t.llm_scores[BASIC_VALUES].to_numpy(float)
    ks = list(range(2, 9))
    ksel = ebene2.k_selection(xh, xl, seed)
    null_sil = gaussian_null_silhouette(xh, ks, seed)
    null_sil_l = gaussian_null_silhouette(xl, ks, seed)   # eigener Vergleich für die Twins (gleiche Kovarianz wie sie)
    bic =pd.DataFrame([{"k": k, "bic_mensch": lpa(xh, k, seed).bic(xh), "bic_llm": lpa(xl, k, seed).bic(xl)}
                        for k in range(1, 7)])
    sil_h = ksel[ksel.daten == "mensch"].set_index("k")["silhouette"]
    null2 = null_sil.set_index("k").loc[2, "mean"]
    kz("2.0", "Silhouette k-Means Mensch (k=2)", sil_h.loc[2], f"Null ohne Cluster {null2:.3f}")
    kz("2.0", "Silhouette k-Means LLM (k=2)", ksel[ksel.daten == "llm"].set_index("k").loc[2, "silhouette"],
       f"Null nach Vorbild der Twins {null_sil_l.set_index('k').loc[2, 'mean']:.3f}")
    kz("2.0", "Silhouette Null nach Vorbild der Twins (k=2)", null_sil_l.set_index("k").loc[2, "mean"])
    kz("2.0", "k mit max. Silhouette (Mensch)", int(sil_h.idxmax()))

    gh, gl = lpa(xh, K, seed), lpa(xl, K, seed)
    lab_h = gh.predict(xh)
    inv = matched(gh.means_, gl.means_)
    lab_l = inv[gl.predict(xl)]
    # Milieus nach Größe der menschlichen Gruppen nummerieren (Milieu 1 = größtes)
    order = np.argsort(-np.bincount(lab_h, minlength=K))
    ren = np.empty(K, int)
    ren[order] = np.arange(K)
    lab_h, lab_l = ren[lab_h], ren[lab_l]
    # 2.0 rechnet die Silhouette mit k-Means, die Milieus kommen aus der LPA: Silhouette auch für die LPA-Lösung
    kz("2.0", "Silhouette LPA-Lösung Mensch (k=2)", silhouette_score(xh, lab_h))
    kz("2.0", "Silhouette LPA-Lösung LLM (k=2)", silhouette_score(xl, lab_l))
    lab_l_proj = ren[gh.predict(xl)]   # LLM-Twins dem menschlichen Modell zugeordnet
    ch = np.array([xh[lab_h == c].mean(0) for c in range(K)])
    cl = np.array([xl[lab_l == c].mean(0) for c in range(K)])
    names = milieu_names(ch)
    km_h = ebene2.kmeans(xh, K, seed)
    km_l = ebene2.kmeans(xl, K, seed)
    km_inv = matched(km_h.cluster_centers_, km_l.cluster_centers_)
    km_lab_l = km_inv[km_l.labels_]
    twins["cluster_mensch"] = lab_h + 1
    twins["cluster_twin"] = lab_l + 1
    twins["cluster_twin_frei_k"] = None  # frei geschätztes k unten

    # Lage, Streuung, Form je Milieu und gesamt
    groups = [("gesamt", xh, xl)] + [(f"Milieu {c + 1}", xh[lab_h == c], xl[lab_l == c]) for c in range(K)]
    m_rows = []
    for name, a, b in groups:
        ca, cb = np.cov(a, rowvar=False), np.cov(b, rowvar=False)
        sh = ebene2.split_half(a, rng)
        m_rows.append({"gruppe": name, "n_mensch": len(a), "n_llm": len(b),
                       "zentroid_abstand": float(np.linalg.norm(a.mean(0) - b.mean(0))),
                       "ref_zentroid_abstand": sh["ref_zentroid_abstand"],
                       "tr_mensch": float(np.trace(ca)), "tr_llm": float(np.trace(cb)),
                       "bures_wasserstein": ebene2.bures_wasserstein(ca, cb),
                       "ref_bures_wasserstein": sh["ref_bures_wasserstein"], "ref_mmd2": sh["ref_mmd2"]})
    metr = pd.DataFrame(m_rows)
    mmd_res = {}
    for name, a, b in groups:
        o, null, p = mmd_null(a, b, rng)
        mmd_res[name] = (o, null, p)
    metr["mmd2"] = [mmd_res[g][0] for g in metr["gruppe"]]
    metr["mmd_p"] = [mmd_res[g][2] for g in metr["gruppe"]]
    metr["tr_verhaeltnis"] = metr["tr_llm"] / metr["tr_mensch"]
    xle = value_scores(le)   # Werte der Twins aus Erwartungswerten statt gezogenen Antworten
    metr["tr_llm_erwartung"] = [float(np.trace(np.cov(b, rowvar=False)))
                                for b in [xle] + [xle[lab_l == c] for c in range(K)]]
    metr["tr_verhaeltnis_erwartung"] = metr["tr_llm_erwartung"] / metr["tr_mensch"]
    between_h = float(np.linalg.norm(ch[0] - ch[1]))
    # Robustheit gegen den Seed der Ziehung: 20 neue Ziehungen aus denselben Wahrscheinlichkeitsvektoren
    rng_draw = np.random.default_rng(seed + 3)
    tr_h = float(metr.loc[metr.gruppe == "gesamt", "tr_mensch"].iloc[0])
    re_mae, re_tr, draws = [], [], []
    for _ in range(20):
        d = redraw(lp, rng_draw)
        draws.append(d)
        re_mae.append(np.abs(d - h).mean())
        re_tr.append(np.trace(np.cov(value_scores(d), rowvar=False)) / tr_h)
    kz("1a", "MAE Twin gezogen, 20 neue Ziehungen (Mittel)", float(np.mean(re_mae)),
       f"Spanne {min(re_mae):.3f}–{max(re_mae):.3f}")
    kz("2b", "tr(Σ) Mensch/LLM gesamt, 20 neue Ziehungen (Mittel)", float(np.mean(re_tr)),
       f"Spanne {min(re_tr):.3f}–{max(re_tr):.3f}")
    for r in metr.itertuples():
        kz("2a", f"Zentroid-Abstand {r.gruppe}", r.zentroid_abstand, f"Split-Half {r.ref_zentroid_abstand:.3f}")
        kz("2b", f"tr(Σ) Mensch/LLM {r.gruppe}", r.tr_verhaeltnis, f"{r.tr_mensch:.2f} / {r.tr_llm:.2f}")
        kz("2b", f"Bures-Wasserstein {r.gruppe}", r.bures_wasserstein, f"Split-Half {r.ref_bures_wasserstein:.3f}")
        kz("2b", f"tr(Σ) Mensch/LLM-Erwartungswerte {r.gruppe}", r.tr_verhaeltnis_erwartung,
           f"{r.tr_mensch:.2f} / {r.tr_llm_erwartung:.2f}")
        kz("2c", f"MMD² {r.gruppe}", r.mmd2, f"Split-Half {r.ref_mmd2:.4f}, p {r.mmd_p:.3f}")
    kz("2a", "Abstand der menschlichen Milieus untereinander", between_h)
    for c in range(K):
        kz("2a", f"Anteil Milieu {c + 1} Mensch / LLM", float(np.mean(lab_h == c)), f"{np.mean(lab_l == c):.3f}")

    ari = adjusted_rand_score(lab_h, lab_l)
    ari_proj = adjusted_rand_score(lab_h, lab_l_proj)
    ari_km = adjusted_rand_score(km_h.labels_, km_lab_l)
    ari_null = np.array([adjusted_rand_score(lab_h, rng.permutation(lab_l)) for _ in range(N_PERM)])
    jac, jac0 = jaccard(lab_h, lab_l, K), jaccard_chance(lab_h, lab_l, K, rng)
    kz("2d", "ARI LPA (eigene Modelle)", ari, f"Null 95-%-Quantil {np.quantile(ari_null, .95):.4f}")
    kz("2d", "ARI LPA (Twins im menschlichen Modell)", ari_proj)
    kz("2d", "ARI k-Means (Robustheit)", ari_km)
    kz("2d", "Twin im Milieu seiner Person", float(np.mean(lab_h == lab_l)),
       f"Zufall {np.sum(np.bincount(lab_h, minlength=K) * np.bincount(lab_l, minlength=K)) / n**2:.3f}")
    for c in range(K):
        kz("2d", f"Jaccard Milieu {c + 1}", jac[c], f"Zufall {jac0[c]:.3f}")
    # Robustheit: liegen Spaltung (2.0) und schlechte Zuordnung (2d) an der Ziehung? Dieselbe Rechnung mit Erwartungswerten
    kz("2.0", "Silhouette k-Means LLM-Erwartungswerte (k=2)",
       silhouette_score(xle, ebene2.kmeans(xle, 2, seed).labels_), "gezogen siehe ksel")
    g_le = lpa(xle, K, seed)
    lab_le = ren[matched(gh.means_, g_le.means_)[g_le.predict(xle)]]
    kz("2d", "Twin im Milieu seiner Person (Erwartungswerte)", float(np.mean(lab_h == lab_le)))
    kz("2d", "ARI LPA (Erwartungswerte)", adjusted_rand_score(lab_h, lab_le))
    # frei geschätztes k für die Twins (BIC der LPA), nur berichtet
    k_free = int(bic.loc[bic["bic_llm"].idxmin(), "k"])
    twins["cluster_twin_frei_k"] = lpa(xl, k_free, seed).predict(xl) + 1
    kz("2.0", "LPA-BIC bestes k Mensch / LLM", int(bic.loc[bic["bic_mensch"].idxmin(), "k"]), f"LLM {k_free}")

    # ===================== 1d (braucht die Milieus) =====================
    demo = t.demo.copy()
    demo["Werte-Milieu"] = pd.Series([names[c] for c in lab_h], index=t.demo.index)
    sub = subgroup_stats(twins, demo)
    for r in sub["tests"].itertuples():
        kz("1d", f"ANOVA MAE ~ {r.merkmal}: η²", r.eta2, f"p(Holm) {r.p_holm:.4f}, Kruskal p {r.kruskal_p:.4f}")
    X = demo_design(t)
    ok = X.notna().all(axis=1).to_numpy()
    coef, r2, f_, pf = ols(twins["mae"].to_numpy()[ok], X[ok])
    coef["p_holm"] = ebene1.holm(coef["p"].to_numpy())
    kz("1d", "Regression MAE ~ Demografie R²", r2, f"F {f_:.2f}, {_pval(pf)}, n {ok.sum()}")

    # ===================== Sensitivitätsanalyse: Ebene 1 mit gezogenen Antworten =====================
    sens, aussagen = sensitivitaet_ebene1(t, le, lm, draws, cellp, demo, seed)
    # Kontrolle: die Variante mit Erwartungswerten muss die Zahlen des Berichts ergeben
    se_ = sens.set_index("kennzahl")["erwartungswert"]
    assert np.isclose(se_["MAE fremder Twin"], twins["mae_zufallspaarung"].mean())
    assert np.isclose(se_["ρ individuelle Abweichung Twin (Mittel)"], twins["spearman_abweichung"].mean())
    for r in aussagen.itertuples():
        kz("Sensitivität", f"Aussage hängt von der Wahl ab: {r.aussage}", int(r.haengt_von_wahl_ab),
           f"Erwartungswert {'ja' if r.erwartungswert else 'nein'}, gezogen {'ja' if r.gezogen else 'nein'}, "
           f"in {r.gezogen_anteil_neuziehungen:.0%} der neuen Ziehungen ja")

    # ===================== 1e Varianzkollaps =====================
    vk = varianzkollaps(t, rng, le)
    kz("1e", "Within-Cell-SD Mensch (Mittel Items)", vk["sd_mensch"].mean())
    kz("1e", "Within-Cell-SD LLM (Mittel Items)", vk["sd_llm"].mean())
    kz("1e", "Items mit LLM-SD unter Bootstrap-2,5-%", int((vk["sd_llm"] < vk["boot_unten"]).sum()))
    kz("1e", "Items mit LLM-SD über Bootstrap-97,5-%", int((vk["sd_llm"] > vk["boot_oben"]).sum()))
    kz("1e", "Within-Cell-SD LLM-Erwartungswerte (Mittel Items)", vk["sd_llm_erwartung"].mean())
    kz("1e", "Items mit SD der LLM-Erwartungswerte unter Bootstrap-2,5-%",
       int((vk["sd_llm_erwartung"] < vk["boot_unten"]).sum()))
    vz = varianzzerlegung(h, le, lvar)
    kz("1e", "Varianz zwischen Twin-Erwartungswerten (Mittel Items)", vz["var_zwischen"].mean())
    kz("1e", "Varianz durch die Ziehung (Mittel Items)", vz["var_ziehung"].mean())
    kz("1e", "Varianz der echten Antworten (Mittel Items)", vz["var_mensch"].mean())
    kz("1e", "Anteil Varianz zwischen Twins an Twin-Gesamtvarianz",
       vz["var_zwischen"].sum() / vz["var_twin_gesamt"].sum())

    # ===================== Fazit 3 Werte oder Demografie =====================
    # Twins gezogen (untere Schranke: Ziehungsrauschen ist nicht demografisch erklärbar) und mit Erwartungswerten
    # (obere Schranke: entrauschte Twins gegen Personen mit Messfehler).
    r2_rows = []
    for v in BASIC_VALUES + ["x", "y"]:
        okv = ok
        r2h = ols(t.human_scores[v].to_numpy()[okv], X[okv])[1]
        r2l = ols(t.llm_scores[v].to_numpy()[okv], X[okv])[1]
        r2e = ols(xle[okv, BASIC_VALUES.index(v)], X[okv])[1] if v in BASIC_VALUES else np.nan
        r2_rows.append({"wert": v, "r2_mensch": r2h, "r2_llm": r2l, "r2_llm_erwartung": r2e})
    r2df = pd.DataFrame(r2_rows)
    # Faktoren Twin / Person sind Quotienten kleiner R²: 95-%-Intervalle per Bootstrap über Personen (gepaart)
    Xo = X[ok].reset_index(drop=True)
    yh_, yl_, ye_ = (np.asarray(a, float)[ok] for a in (t.human_scores[BASIC_VALUES], t.llm_scores[BASIC_VALUES], xle))
    rng_r2 = np.random.default_rng(seed + 4)
    fb = {v: ([], []) for v in BASIC_VALUES}
    for _ in range(500):
        i = rng_r2.integers(0, len(Xo), len(Xo))
        Xi = Xo.iloc[i]
        for j, v in enumerate(BASIC_VALUES):
            rh_ = ols(yh_[i, j], Xi)[1]
            fb[v][0].append(ols(yl_[i, j], Xi)[1] / rh_)
            fb[v][1].append(ols(ye_[i, j], Xi)[1] / rh_)
    for col, k_ in [("faktor_gezogen", 0), ("faktor_erwartung", 1)]:
        r2df[f"{col}_ci_unten"] = r2df.wert.map(lambda v, k_=k_: np.quantile(fb[v][k_], .025) if v in fb else np.nan)
        r2df[f"{col}_ci_oben"] = r2df.wert.map(lambda v, k_=k_: np.quantile(fb[v][k_], .975) if v in fb else np.nan)
    kz("Fazit 3", "Werte mit Faktor gezogen gesichert > 1 (Bootstrap)",
       int((r2df.faktor_gezogen_ci_unten > 1).sum()))
    for r in r2df.itertuples():
        kz("Fazit 3", f"R² Demografie → {r.wert} Mensch / LLM", r.r2_mensch, f"{r.r2_llm:.3f}")
        if r.wert in BASIC_VALUES:
            kz("Fazit 3", f"R² Demografie → {r.wert} LLM-Erwartungswerte", r.r2_llm_erwartung)
    # R² überzeichnet den Abstand, weil die Twin-Erwartungswerte weniger Gesamtvarianz haben: absolut erklärte
    # Varianz (R² × Varianz), summiert über die zehn Werte
    def erklaert(y_all):
        return sum(ols(y_all[ok, j], X[ok])[1] * y_all[ok, j].var(ddof=1) for j in range(len(BASIC_VALUES)))
    ev_h = erklaert(t.human_scores[BASIC_VALUES].to_numpy(float))
    ev_l = erklaert(t.llm_scores[BASIC_VALUES].to_numpy(float))
    ev_e = erklaert(xle)
    kz("Fazit 3", "Demografisch erklärte Varianz (Summe Werte) Mensch / LLM-Erwartungswerte", ev_h, f"{ev_e:.3f}")
    kz("Fazit 3", "Demografisch erklärte Varianz (Summe Werte) LLM gezogen", ev_l)
    kz("Fazit 3", "Verhältnis erklärte Varianz LLM-Erwartungswerte / Mensch", ev_e / ev_h, f"gezogen {ev_l / ev_h:.2f}")
    # Milieuzugehörigkeit aus der Demografie (lineares Wahrscheinlichkeitsmodell, Milieu 2 vs. 1 bei K = 2)
    r2_mil = {nm: ols((lab[ok] == 1).astype(float), X[ok])[1]
              for nm, lab in [("Mensch", lab_h), ("LLM", lab_l), ("LLM-Erwartungswerte", lab_le)]}
    kz("Fazit 3", "R² Demografie → Milieuzugehörigkeit Mensch / LLM", r2_mil["Mensch"], f"{r2_mil['LLM']:.3f}")
    kz("Fazit 3", "R² Demografie → Milieuzugehörigkeit LLM-Erwartungswerte", r2_mil["LLM-Erwartungswerte"])

    # ===================== Abbildungen =====================
    pid = "DE_50032" if "DE_50032" in t.ids else t.ids[0]
    i = t.ids.index(pid)
    P.fig_a1(pid, h[i], lm[i], le[i], lp[i], t.question_no, run_dir.name, fig_dir)
    w_mae = stats.wilcoxon(twins["mae"], twins["mae_zufallspaarung"]).pvalue
    w_rho = stats.wilcoxon(twins["spearman_abweichung"], twins["spearman_abweichung_zufallspaarung"],
                           nan_policy="omit").pvalue
    P.fig_1a({"Fremder Twin": twins["mae_zufallspaarung"].mean(),
              "Twin": twins["mae"].mean(),
              "Demografie-Mittelwert": twins["mae_zellmittel"].mean(),
              "Mittelwert aller Personen": twins["mae_mittelprofil"].mean()},
             twins["mae_gezogen"].mean(), w_mae, n, fig_dir)
    w_rho_cell = stats.wilcoxon(twins["spearman_abweichung"], twins["spearman_abweichung_zellmittel"],
                                nan_policy="omit").pvalue
    P.fig_1b({"Twin": (twins["spearman"].mean(), twins["spearman_abweichung"].mean()),
              "Demografie-Mittelwert": (twins["spearman_zellmittel"].mean(),
                                        twins["spearman_abweichung_zellmittel"].mean()),
              "Fremder Twin": (twins["spearman_zufallspaarung"].mean(),
                               twins["spearman_abweichung_zufallspaarung"].mean())}, w_rho, w_rho_cell, n, fig_dir)
    P.fig_a3(twins, n, fig_dir)
    P.fig_1b2(items, t.question_no, n, fig_dir)
    P.fig_1c(items, t.question_no, n, fig_dir)
    P.fig_1d(sub["gruppen"], sub["tests"], twins["mae"].mean(), n, fig_dir)
    P.fig_1e(vk, t.question_no, fig_dir)
    P.fig_a2(vz, t.question_no, n, fig_dir)
    P.fig_20(ksel, null_sil, null_sil_l, n, fig_dir)
    P.fig_21(t.human_scores[["x", "y"]].to_numpy(float), t.llm_scores[["x", "y"]].to_numpy(float),
             lab_h, lab_l, names, n, fig_dir)
    g_ = metr.set_index("gruppe")
    P.fig_2a(ch, cl, [np.mean(lab_h == c) for c in range(K)], [np.mean(lab_l == c) for c in range(K)], names,
             g_.loc["gesamt", "zentroid_abstand"], g_.loc["gesamt", "ref_zentroid_abstand"],
             [g_.loc[f"Milieu {c + 1}", "zentroid_abstand"] for c in range(K)], between_h, n, fig_dir)
    P.fig_2b(metr, names, n, fig_dir)
    P.fig_2c(xh, xl, max(r[2] for r in mmd_res.values()), n, fig_dir)
    P.fig_2d(ebene2.contingency(lab_h, lab_l, K), float(np.mean(lab_h == lab_l)),
             float(np.sum(np.bincount(lab_h, minlength=K) * np.bincount(lab_l, minlength=K)) / n**2), ari,
             names, fig_dir)
    P.fig_fazit3(r2df, int(ok.sum()), fig_dir)
    null_sil_l.to_csv(out / "silhouette_null_twins.csv", index=False)

    # ===================== Tabellen =====================
    pd.DataFrame(K_).to_csv(out / "kennzahlen.csv", index=False)
    twins.to_csv(out / "twins.csv")
    items.to_csv(out / "items.csv", index=False)
    sub["gruppen"].to_csv(out / "subgruppen.csv", index=False)
    sub["tests"].to_csv(out / "subgruppen_tests.csv", index=False)
    coef.to_csv(out / "regression_mae.csv", index=False)
    vk.to_csv(out / "varianzkollaps.csv", index=False)
    vz.to_csv(out / "varianzzerlegung.csv", index=False)
    metr.to_csv(out / "milieus.csv", index=False)
    bic.to_csv(out / "lpa_bic.csv", index=False)
    r2df.to_csv(out / "demografie_r2.csv", index=False)
    sens.to_csv(out / "sensitivitaet_ebene1.csv", index=False)
    aussagen.to_csv(out / "sensitivitaet_aussagen.csv", index=False)
    write_report(out, run_dir.name, n, pd.DataFrame(K_), items, sub["tests"], coef, vk, metr, r2df,
                 names, sens, aussagen)
    return out


def write_report(out, name, n, kz, items, tests, coef, vk, metr, r2df, names, sens, aussagen) -> None:
    v = {r.kennzahl: r.wert for r in kz.itertuples()}
    def pct(x):
        return f"{x * 100:.0f} %"
    g = metr.set_index("gruppe")
    under = items[items.signifikant & (items.me < 0)].sort_values("me").head(4)
    over = items[items.signifikant & (items.me > 0)]
    sig_groups = tests[tests.p_holm < 0.05].sort_values("eta2", ascending=False)
    r2b = r2df[r2df.wert.isin(BASIC_VALUES)]
    f_erwartung = (r2b.r2_llm_erwartung / r2b.r2_mensch).max()
    # Rangfolge nach Abstand in Prozentpunkten (der Quotient ist bei kleinem R² der Personen instabil)
    top_r2 = r2b.assign(d=r2b.r2_llm_erwartung - r2b.r2_mensch).sort_values("d", ascending=False).head(3)
    f_gezogen = (r2b.r2_llm / r2b.r2_mensch).max()
    def fig(f):
        return f"![{f}](figures/{f}.png)"
    def desc(text):
        return f"*Beschreibung.* {text}"
    kzi = kz.set_index("kennzahl")
    m1_llm = float(kzi.loc["Anteil Milieu 1 Mensch / LLM", "vergleich"])
    chance = float(kzi.loc["Twin im Milieu seiner Person", "vergleich"].split()[-1])
    vn = P.VALUE_NAME
    share_between = v["Anteil Varianz zwischen Twins an Twin-Gesamtvarianz"]
    mae, mae_g = v["MAE LLM-Twin"], v["MAE Twin gezogen"]
    mae_cell, mae_pop = v["MAE Demografie-Zellmittel"], v["MAE Mittelprofil (ESS-Durchschnitt)"]
    rho_dev, rho_dev_cell = v["ρ Abweichungsprofil LLM-Twin (Mittel)"], v["ρ Abweichungsprofil Zellmittel (Mittel)"]
    dev_better = rho_dev > rho_dev_cell
    dev_tie = abs(rho_dev - rho_dev_cell) < 0.05   # bei N = 2 262 signifikant, praktisch gleichauf
    n_items_better = int(v["Items mit LLM-ρ > Zellmittel-ρ"])
    close = items.loc[(items.spearman_item - items.spearman_item_zellmittel).abs() < 0.01, "item"].tolist()
    better_cell = v["Anteil Twins genauer als Demografie-Zellmittel"]
    better_dev = v["Anteil Twins mit Abweichungs-ρ > Zellmittel"]
    dist, between_h = g.loc["gesamt", "zentroid_abstand"], v["Abstand der menschlichen Milieus untereinander"]
    n_dep = int(aussagen.haengt_von_wahl_ab.sum())
    def wert(x, k):
        return _de(x, 3) if k.startswith(("ρ", "Differenz", "ME", "η²", "MAE", "RMSE", "Regression")) else (
            pct(x) if k.startswith("Anteil") else _pval(x) if k.endswith(" p") else f"{x:.0f}")
    L = [
        f"# Auswertung entlang der Forschungsfragen: {name}",
        "",
        f"{n} Twin-Paare (ESS 11 DE ↔ Twin). Items umgepolt (6 = sehr wichtig), Fehler = Twin − Person. "
        "Erzeugt mit `python -m ess_pipeline.analysis.forschungsfragen`. Alle Kennzahlen: `kennzahlen.csv`, "
        "je Twin (`mae`, `mae_gezogen`, `spearman`, `cluster_twin`, …): `twins.csv`.",
        "",
        "**Datengrundlage.** Gezogene Antwort = die Antwort, die aus den sechs Wahrscheinlichkeiten des Modells "
        "ausgelost wurde; Erwartungswert = Σ k · pk, der Schwerpunkt dieser Wahrscheinlichkeiten ohne Zufall der "
        "Ziehung. **Ebene 1 rechnet mit Erwartungswerten:** Mittelwert und Demografie-Mittelwert sind selbst "
        "Erwartungswerte, gegen die gezogene Antwort trüge nur der Twin das Rauschen der Ziehung, und das enthält per "
        "Konstruktion keine Information über die Person. Der fremde Twin wird ebenfalls aus Erwartungswerten gebildet. "
        "**Ebene 2 rechnet mit gezogenen Antworten,** denn dort geht es um die synthetische Stichprobe als Datensatz. "
        "Beide Varianten stehen nur dort nebeneinander, wo der Unterschied selbst der Befund ist (1a, 1e, A2, 2b, "
        "Fazit 3). In Fazit 3 sind gezogene Antworten die untere, Erwartungswerte die obere Schranke. Der "
        "Erwartungswert ist nur dann die passende Punktprognose, wenn die verbalisierten Wahrscheinlichkeiten halbwegs "
        "kalibriert sind. **Ebene 1 steht im Anhang vollständig auch mit gezogenen Antworten (Sensitivitätsanalyse);** "
        f"{n_dep} von {len(aussagen)} geprüften Aussagen hängen von dieser Wahl ab, alle beim Vergleich mit dem "
        "Demografie-Mittelwert in 1b, A3 und 1b′.",
        "",
        "**Vergleichsgrößen in Ebene 1.** Der *fremde Twin* (Twin einer anderen Person) ist die Untergrenze: Twin und "
        "fremder Twin teilen Modell, Prompt und systematischen Fehler, der Unterschied ist also die Wirkung des "
        "Profils. Der *Demografie-Mittelwert* (mittlere Antwort der anderen Personen gleichen Geschlechts, Alters und "
        "Bildungsgrads) ist die Messlatte: Weiß der Twin mehr als drei Merkmale? Er kennt nichts über die Person, aber "
        "die echten Antworten aller anderen Befragten, die dem Modell fehlen. Der Mittelwert aller Personen steht nur "
        "in 1a als anschaulicher Bezug.",
        "",
        "| Nr. | Abbildung | Kurzantwort |",
        "|---|---|---|",
        "| A1 Beispielperson | `A1_beispielperson` | So entsteht ein Twin: sechs Wahrscheinlichkeiten je Frage, daraus "
        "eine gezogene Antwort |",
        f"| 1a Genauigkeit | `FF1a_genauigkeit` | MAE {_de(mae)} (gezogen {_de(mae_g)}); besser als fremder Twin "
        f"({_de(v['MAE Zufallspaarung (fremder Twin)'])}), schlechter als Demografie-Mittelwert ({_de(mae_cell)}) "
        f"und Mittelwert ({_de(mae_pop)}) |",
        f"| 1b Profil | `FF1b_profil` | ρ̄ = {_de(v['ρ Profil LLM-Twin (Mittel)'])}; individuelle Abweichung "
        f"ρ̄ = {_de(rho_dev)} ({'gleichauf mit' if dev_tie else 'über' if dev_better else 'unter'} dem Demografie-Mittelwert {_de(rho_dev_cell)}) |",
        f"| A3 Fehler je Twin | `A3_fehler_je_twin` | {pct(better_cell)} der Twins genauer als der "
        f"Demografie-Mittelwert, bei der individuellen Abweichung {pct(better_dev)} besser |",
        f"| 1c Bias | `FF1c_bias` | {int(v['Items mit signifikantem Bias (Holm)'])}/21 Fragen gerichtet, davon "
        f"{int(v['davon unterschätzt'])} unterschätzt |",
        f"| A2 Varianzzerlegung | `A2_varianzzerlegung` | nur {pct(share_between)} der Twin-Varianz unterscheidet "
        "die Twins voneinander, der Rest ist Zufall der Ziehung |",
        f"| 2.0 Milieus | `FF2_0_milieus_existenz` | Silhouette Personen "
        f"{_de(v['Silhouette k-Means Mensch (k=2)'], 3)} = Zufallsdaten ohne Gruppen → Kontinuum; Twins spalten sich; "
        "k = 2 gesetzt |",
        f"| 2.1 Milieus im Wertekreis | `FF2_1_milieus` | {names[0]} oben, {names[1]} unten; Twins streuen weiter "
        "und rutschen Richtung Bewahrung |",
        f"| 2a Lage | `FF2a_lage` | Twins um {_de(dist)} verschoben = {pct(dist / between_h)} des Abstands der "
        f"Personen-Milieus; Milieu-Größen kippen ({names[0]}: Personen {pct(v['Anteil Milieu 1 Mensch / LLM'])}, "
        f"Twins {pct(m1_llm)}) |",
        f"| 2b Streuung | `FF2b_streuung` | tr(Σ) Twin/Person × {_de(g.loc['gesamt', 'tr_verhaeltnis'])} (gezogen), "
        f"× {_de(g.loc['gesamt', 'tr_verhaeltnis_erwartung'])} (Erwartungswerte) |",
        f"| 2d Zuordnung | `FF2d_zuordnung` | {pct(v['Twin im Milieu seiner Person'])} im Milieu der Person "
        f"(Zufall {pct(chance)}); ARI {_de(v['ARI LPA (eigene Modelle)'], 3)} |",
        f"| Fazit 3 Werte oder Demografie | `Fazit3_werte_oder_demografie` | Demografie erklärt bei den Twins mehr "
        f"Wertevarianz: gezogen bis {_de(f_gezogen, 1)}×, Erwartungswerte bis {_de(f_erwartung, 1)}×; "
        f"größter Abstand: {', '.join(vn[w] for w in top_r2.wert)} |",
        f"| *Anhang* 1b′ Trennschärfe | `FF1b2_trennschaerfe` | ρ̄ über Personen = "
        f"{_de(v['spearman_item Mittel LLM'])}; {n_items_better}/21 Fragen besser als der Demografie-Mittelwert |",
        "| *Anhang* 1d Subgruppen | `FF1d_subgruppen` | signifikant: "
        + (", ".join(f"{r.merkmal} (η² = {_de(r.eta2, 3)})" for r in sig_groups.itertuples()) or "keine")
        + f"; Demografie erklärt R² = {_de(v['Regression MAE ~ Demografie R²'] * 100, 1)} % des MAE |",
        f"| *Anhang* 1e Varianzkollaps | `FF1e_varianzkollaps` | gezogene Antworten streuen bei "
        f"{int(v['Items mit LLM-SD über Bootstrap-97,5-%'])} Fragen weiter als bei Personen, die Erwartungswerte bei "
        f"{int(v['Items mit SD der LLM-Erwartungswerte unter Bootstrap-2,5-%'])} Fragen enger |",
        f"| *Anhang* 2c Form | `FF2c_form` | MMD² {_de(g.loc['gesamt', 'mmd2'], 4)}, p ≤ "
        f"{_de(g.loc['gesamt', 'mmd_p'], 3)} |",
        f"| *Anhang* Sensitivität | – | Ebene 1 mit gezogenen Antworten: {n_dep} von {len(aussagen)} Aussagen hängen "
        "von der Wahl ab, alle beim Vergleich mit dem Demografie-Mittelwert (1b, A3, 1b′) |",
        "",
        "## Ebene 1 · Twin ↔ Person",
        "",
        "### A1 Beispielperson",
        fig("A1_beispielperson"),
        "",
        desc("Für jede Frage gibt das Modell sechs Wahrscheinlichkeiten an; ein Programm lost daraus die Antwort des "
             "Twins aus. Der Erwartungswert Σ k · pk ist der Schwerpunkt dieser Wahrscheinlichkeiten, die gezogene "
             "Antwort kann zufällig weit davon entfernt liegen. Links stehen die 21 Antworten der Person (blau) und "
             "ihres Twins (orange gefüllt = gezogen, Ring = Erwartungswert), die graue Linie ist der Fehler; rechts sind drei Fragen "
             "aufgeschlüsselt. Alle folgenden Abbildungen sind Zusammenfassungen solcher Paare."),
        "",
        "### 1a Absolute Genauigkeit",
        fig("FF1a_genauigkeit"),
        "",
        desc(f"Der Twin liegt im Mittel {_de(mae)} Skalenpunkte neben der Antwort seiner Person, mit gezogenen "
             f"Antworten {_de(mae_g)}; die Differenz ist allein der Preis der Ziehung. Der MAE ist der mittlere "
             "Abstand zwischen Twin- und Personenantwort in Skalenpunkten; die grauen Vergleichsgrößen wissen nichts "
             "über die Person. Kürzere Balken bedeuten genauer."),
        "",
        f"Der Twin ist genauer als ein fremder Twin ({_de(v['MAE Zufallspaarung (fremder Twin)'])}; "
        f"{pct(v['Anteil Twins genauer als Zufallspaarung'])} der Twins sind genauer, Wilcoxon "
        f"{_pval(v['Wilcoxon Twin vs. Zufallspaarung p'])}), aber {'schlechter' if mae > mae_cell else 'besser'} als "
        f"der Demografie-Mittelwert ({_de(mae_cell)}) und der Mittelwert aller Personen ({_de(mae_pop)}). Das liegt "
        "nicht an der Ziehung: Verglichen werden hier Erwartungswerte mit Erwartungswerten. Zum Vergleich: Würfeln "
        f"ergäbe {_de(v['MAE Zufall 1–6'])}.",
        "",
        "### 1b Profilähnlichkeit",
        fig("FF1b_profil"),
        "",
        desc(f"Der Twin trifft die Rangfolge der 21 Fragen mit ρ̄ = {_de(v['ρ Profil LLM-Twin (Mittel)'])}, die "
             f"individuelle Abweichung mit ρ̄ = {_de(rho_dev)}. Spearman ρ vergleicht die Rangfolge der Fragen zwischen "
             "Twin und Person (1 = gleiche Rangfolge, 0 = kein Zusammenhang). Die rechte Gruppe gibt es, weil fast "
             "alle Personen Wohlwollen wichtig und Macht unwichtig finden; darum erreicht links schon der fremde Twin "
             f"{_de(v['ρ Profil Zufallspaarung (Mittel)'])}, rechts ist dieser gemeinsame Teil abgezogen."),
        "",
        f"Nach Abzug des Mittelwerts je Frage bleibt ρ̄ = {_de(rho_dev)} (fremder Twin "
        f"{_de(v['ρ Abweichungsprofil Zufallspaarung (Mittel)'])}, "
        f"{_pval(v['Wilcoxon Abweichungs-ρ Twin vs. Zufallspaarung p'])}). **Der Twin enthält also Information über "
        f"die Person**, {'etwa so viel' if dev_tie else 'mehr' if dev_better else 'aber weniger'}, wie der Demografie-Mittelwert trägt "
        f"(ρ̄ = {_de(rho_dev_cell)}). Mit gezogenen Antworten wären es nur "
        f"{_de(v['ρ Abweichungsprofil LLM-Twin gezogen (Mittel)'])}: Das Rauschen der Ziehung verdeckt einen Teil "
        "dieser Information. **Die Rangfolge gegenüber dem Demografie-Mittelwert hängt damit von der Wahl ab:** mit "
        "Erwartungswerten liegt der Twin knapp darüber, mit gezogenen Antworten darunter (Anhang, "
        "Sensitivitätsanalyse). Dass der Twin überhaupt Information über die Person enthält, gilt in beiden Varianten.",
        "",
        "### A3 Fehler je Twin",
        fig("A3_fehler_je_twin"),
        "",
        desc(f"{pct(better_cell)} der Twins liegen näher an ihrer Person als deren Demografie-Mittelwert, bei der "
             f"individuellen Abweichung sind {pct(better_dev)} besser als er. Gezeigt ist je Person die Differenz "
             "Twin minus Vergleichsgröße derselben Person, für den MAE (links) und das ρ der individuellen Abweichung "
             "(rechts); orange gegen den Demografie-Mittelwert, grau gegen den fremden Twin. Die Fläche auf der guten "
             "Seite der 0 ist der Anteil der Twins, die besser sind (links der 0 genauer, rechts der 0 besser)."),
        "",
        "### 1c Systematischer Bias",
        fig("FF1c_bias"),
        "",
        desc(f"Bei {int(v['Items mit signifikantem Bias (Holm)'])} von 21 Fragen liegt der Twin systematisch daneben, "
             f"bei {int(v['davon unterschätzt'])} davon nach unten. Mean Error = Twin minus Person mit Vorzeichen; "
             "negativ heißt, der Twin hält den Wert für unwichtiger; −1 ist ein ganzer Punkt auf einer 6er-Skala. "
             "Gezogene Antworten haben in Erwartung denselben Mean Error. Signifikanz mit t-Test und Holm-Korrektur "
             "über 21 Fragen; die schwarzen Linien sind 95-%-Konfidenzintervalle, die Farbe zeigt nur die Richtung, "
             "blasse Balken sind nicht signifikant."),
        "",
        f"Mean Error gesamt {_de(v['ME gesamt'])}. Am stärksten unterschätzt: "
        + ", ".join(f"Q{r.frage[1:]} {P.ITEM_SHORT[r.item]} ({vn[r.wert]}, ME {_de(r.me)}, d = {_de(r.cohens_d)})"
                    for r in under.itertuples())
        + ". Überschätzt: " + ", ".join(f"{P.ITEM_SHORT[r.item]} ({vn[r.wert]}, ME {_de(r.me)})"
                                        for r in over.itertuples())
        + ". Das Muster (Hedonismus, Leistung, Stimulation runter, Konformität hoch) passt zum Bild einer "
        "„vernünftigen, angepassten“ Durchschnittsperson. Diese gerichteten Fehler erklären, warum der Twin beim MAE "
        "hinter dem Demografie-Mittelwert bleibt, obwohl er die Rangfolge der Person etwas besser kennt (1b).",
        "",
        "### A2 Varianzzerlegung",
        fig("A2_varianzzerlegung"),
        "",
        desc(f"Nur rund {pct(share_between)} der Streuung der Twins unterscheidet die Twins voneinander; der Rest "
             "ist Zufall der Ziehung. Nach dem Satz von der totalen Varianz ist die Varianz der gezogenen Antworten "
             "die Varianz der Erwartungswerte zwischen den Twins plus die mittlere Varianz innerhalb eines "
             "Wahrscheinlichkeitsvektors (Doku 4.7.4). Kräftig = zwischen den Twins, blass = Ziehung, blauer Punkt = "
             "Varianz der Personen; die Zahl ist der Anteil zwischen den Twins."),
        "",
        f"Varianz je Frage im Mittel: Personen {_de(v['Varianz der echten Antworten (Mittel Items)'])}, Twins "
        f"zwischen den Erwartungswerten {_de(v['Varianz zwischen Twin-Erwartungswerten (Mittel Items)'])} und durch "
        f"die Ziehung {_de(v['Varianz durch die Ziehung (Mittel Items)'])}. Einschränkung: Auch die Antworten der "
        "Personen sind eine einzelne, messfehlerbehaftete Antwort. Gezogen ist der Vergleich Antwort gegen Antwort, "
        "die Erwartungswerte zeigen die Unterschiede zwischen den Twins ohne Ziehung; der Kollaps ist damit eher "
        "etwas überzeichnet.",
        "",
        "## Ebene 2 · Population ↔ Population",
        "",
        "### 2.0 Gibt es Milieus?",
        fig("FF2_0_milieus_existenz"),
        "",
        desc(f"Bei Personen nicht: Ihre Silhouette ({_de(v['Silhouette k-Means Mensch (k=2)'], 2)} bei k = 2) liegt "
             "genau auf der von Zufallsdaten ohne Gruppen, die Twins spalten sich dagegen in zwei Lager "
             f"({_de(v['Silhouette k-Means LLM (k=2)'], 2)}). Die Silhouette misst, wie klar Gruppen getrennt sind "
             "(0 = gar nicht, 1 = perfekt); ein Gruppierungsverfahren findet immer Gruppen, deshalb braucht es die "
             "Prüfung. Die graue Linie zeigt künstliche Daten mit gleicher Streuung und gleichen Zusammenhängen, aber "
             "garantiert ohne Gruppen; was darüber liegt, ist echte Struktur."),
        "",
        "Gegen Zufallsdaten nach Vorbild der Twins (gleiche Kovarianz wie sie) liegen die Twins bei k = 2 nur "
        f"knapp darüber ({_de(v['Silhouette k-Means LLM (k=2)'], 2)} gegen "
        f"{_de(v['Silhouette Null nach Vorbild der Twins (k=2)'], 2)}): Ein Teil der Spaltung liegt an der Form der "
        "Twin-Wolke. Mit Erwartungswerten statt gezogenen Antworten ist die Spaltung der Twins noch deutlicher (Silhouette "
        f"{_de(v['Silhouette k-Means LLM-Erwartungswerte (k=2)'], 2)}): Die Ziehung verwischt sie nur. Auch die LPA mit "
        "voller Kovarianz bevorzugt bei den Personen k = 1; mit diagonaler Kovarianz sinkt das BIC monoton "
        "(`lpa_bic.csv`). Die diagonale LPA nimmt an, dass die Werte innerhalb eines Milieus unabhängig sind; "
        "zentrierte Werte hängen aber per Konstruktion negativ zusammen (der persönliche Mittelwert ist abgezogen). "
        "k = 2 ist deshalb eine Setzung, keine Schätzung; die Milieus sind als Regionen im Kontinuum zu lesen. Die "
        "Silhouette wird mit k-Means gerechnet, die Milieus mit der LPA; für die LPA-Lösung selbst ergibt sich "
        f"praktisch dieselbe Silhouette (Personen {_de(v['Silhouette LPA-Lösung Mensch (k=2)'], 2)}, Twins "
        f"{_de(v['Silhouette LPA-Lösung LLM (k=2)'], 2)}).",
        "",
        "### 2.1 Milieus im Wertekreis",
        fig("FF2_1_milieus"),
        "",
        desc(f"{names[0]} liegt oben, {names[1]} unten; die Twins streuen weiter und rutschen Richtung Bewahrung. Ein "
             "Milieu ist hier eine Gruppe aus der Latent-Profile-Analyse mit k = 2 im Raum der 10 zentrierten Werte, "
             "getrennt für Personen und Twins gebildet, kein soziales Milieu; jedes Twin-Milieu wird dem Personen-"
             "Milieu mit dem nächstgelegenen Mittelpunkt zugeordnet. Achsen: rechts Selbsttranszendenz, links "
             "Selbststärkung, oben Offenheit, unten Bewahrung; weil 10 Werte auf 2 Achsen gezeigt werden, "
             "überlappen die Farben."),
        "",
        "### 2a Lage",
        fig("FF2a_lage"),
        "",
        desc(f"Der Profilverlauf stimmt, die Lage nicht: Der Mittelpunkt aller Twins liegt {_de(dist)} vom Mittelpunkt "
             f"aller Personen entfernt, das sind {pct(dist / between_h)} des Abstands der beiden Personen-Milieus "
             f"untereinander ({_de(between_h)}). Abstand = euklidische Entfernung im 10-dimensionalen Werteraum, "
             f"zwischen den Gesamt-Mittelpunkten (je Milieu {_de(g.loc['Milieu 1', 'zentroid_abstand'])} bzw. "
             f"{_de(g.loc['Milieu 2', 'zentroid_abstand'])}). Die y-Achse zeigt die zentrierte Wichtigkeit, "
             f"0 = persönlicher Durchschnitt aller Werte; Hedonismus wird vor allem in {names[1]} unterschätzt."),
        "",
        f"Das Rauschniveau (Abstand zweier Zufallshälften der Personen, {_de(g.loc['gesamt', 'ref_zentroid_abstand'])}) "
        "zeigt nur, dass der Unterschied echt ist; wie groß er ist, zeigt der Vergleich mit dem Milieuabstand. Die "
        f"Größen kippen: {names[0]} umfasst {pct(v['Anteil Milieu 1 Mensch / LLM'])} der Personen, aber nur "
        f"{pct(m1_llm)} der Twins.",
        "",
        "### 2b Streuung",
        fig("FF2b_streuung"),
        "",
        desc(f"Mit gezogenen Antworten streuen die Twins × {_de(g.loc['gesamt', 'tr_verhaeltnis'])} so stark wie die "
             f"Personen, mit Erwartungswerten nur × {_de(g.loc['gesamt', 'tr_verhaeltnis_erwartung'])}. "
             "Gesamtstreuung = Summe der Varianzen der 10 Werte; 7,2 entspricht einer Standardabweichung von etwa "
             "0,85 je Wert, 10,0 etwa 1,0. Gesamt ist die Streuung größer als innerhalb der Milieus, weil die "
             "Twin-Milieus weiter auseinanderliegen (passt zu 2.0). Der Faktor weicht von A2 ab, weil hier über die "
             "10 Werte summiert wird statt über die 21 Fragen."),
        "",
        f"tr(Σ): Personen {_de(g.loc['gesamt', 'tr_mensch'])}, Twins gezogen {_de(g.loc['gesamt', 'tr_llm'])}, Twins "
        f"Erwartungswerte {_de(g.loc['gesamt', 'tr_llm_erwartung'])}. Bures-Wasserstein (Abstand der ganzen "
        f"Kovarianzmatrizen, nur Anhang): {_de(g.loc['gesamt', 'bures_wasserstein'])}, das "
        f"{_de(g.loc['gesamt', 'bures_wasserstein'] / g.loc['gesamt', 'ref_bures_wasserstein'], 1)}-Fache des Rauschens.",
        "",
        "### 2d Zuordnung",
        fig("FF2d_zuordnung"),
        "",
        desc(f"Kaum öfter als per Zufall: {pct(v['Twin im Milieu seiner Person'])} der Twins landen im Milieu ihrer "
             f"Person, bei zufälliger Zuordnung wären es {pct(chance)} (Anteil Personen × Anteil Twins je Milieu, "
             f"summiert). Beide Milieus liegen nur gut 10 Prozentpunkte über ihrem Zufallswert (dem Anteil der Twins "
             f"im jeweiligen Milieu). ARI = Übereinstimmung der Gruppierung, um Zufall bereinigt (0 = Zufall, 1 = perfekt), hier "
             f"{_de(v['ARI LPA (eigene Modelle)'])}. Zeilen = Milieu der Person, Spalten = Milieu des Twins, Diagonale "
             "= Treffer; Prozent und Farbe zeigen den Anteil an der Zeile."),
        "",
        "Die schlechte Zuordnung liegt nicht an der Ziehung: Mit Erwartungswerten landen "
        f"{pct(v['Twin im Milieu seiner Person (Erwartungswerte)'])} im Milieu ihrer Person (ARI "
        f"{_de(v['ARI LPA (Erwartungswerte)'])}). Robustheit: ARI k-Means {_de(v['ARI k-Means (Robustheit)'], 3)}, "
        f"Twins im Personen-Modell {_de(v['ARI LPA (Twins im menschlichen Modell)'], 3)}; alle über der "
        "Permutations-Null, aber nahe 0.",
        "",
        "## Fazit 3 · Werte oder Demografie?",
        fig("Fazit3_werte_oder_demografie"),
        "",
        desc(f"Eher Demografie: Sechs Merkmale erklären bei den Twins mehr Wertevarianz als bei Personen, mit "
             f"gezogenen Antworten bis {_de(f_gezogen, 1)}-mal, mit Erwartungswerten bis {_de(f_erwartung, 1)}-mal (größter Abstand in Prozentpunkten: "
             f"{', '.join(vn[w] for w in top_r2.wert)}). R² = Anteil der "
             "Unterschiede zwischen Personen in einem Wert, den Geschlecht, Alter, Bildung, Wohnort, Region und "
             "Religion erklären. Ein hoher Twin-Wert heißt: Das Modell leitet Werte stärker aus der Demografie ab als "
             "echte Personen, also stereotyp."),
        "",
        f"Die Abbildung zeigt beide Varianten: gezogene Antworten (bis {_de(f_gezogen, 1)}-mal) als untere Schranke, "
        "weil das Rauschen der Ziehung von der Demografie nicht erklärbar ist und R² drückt; Erwartungswerte als "
        "obere Schranke, weil dann entrauschte Twins mit messfehlerbehafteten Personen verglichen werden. Die sechs "
        "Merkmale stehen selbst im Profil des Twins; ein hoher R² ist deshalb zum Teil konstruktionsbedingt.",
        "",
        "## Antwort auf die Hauptforschungsfrage",
        "",
        "*In welchem Ausmaß reproduzieren LLM-generierte synthetische "
        "Befragte die multivariate Wertestruktur und die daraus abgeleitete personenzentrierte Segmentstruktur einer "
        "realen ESS-PVQ21-Stichprobe?*",
        "",
        f"1. **Person (FF1):** Der Twin liegt im Mittel {_de(mae)} Skalenpunkte daneben, besser als ein fremder Twin, "
        f"aber {'schlechter' if mae > mae_cell else 'besser'} als der Demografie-Mittelwert (1a); "
        f"{pct(better_cell)} der Twins schlagen ihn (A3). Die Rangfolge der Werte einer Person trifft er "
        f"{'etwa so gut wie' if dev_tie else 'besser als' if dev_better else 'schlechter als'} der Demografie-Mittelwert (individuelle Abweichung "
        f"ρ̄ = {_de(rho_dev)} gegen {_de(rho_dev_cell)}, 1b; mit gezogenen Antworten "
        f"{_de(v['ρ Abweichungsprofil LLM-Twin gezogen (Mittel)'])} und damit darunter, siehe Sensitivitätsanalyse). "
        "Beim MAE verliert er wegen gerichteter Fehler: "
        "Hedonismus, Leistung und Stimulation unterschätzt er, Konformität überschätzt er (1c). Das LLM kennt die "
        "Person ein wenig, verschiebt sie aber zur vernünftigen, angepassten Durchschnittsperson.",
        "2. **Population (FF2):** Die Personen bilden ein Kontinuum, die Twins spalten sich in zwei Lager (2.0). Die "
        f"Milieus der Twins liegen verschoben (2a). Die simulierte Population wirkt breiter (tr(Σ) × "
        f"{_de(g.loc['gesamt', 'tr_verhaeltnis'])}, 2b), doch diese Breite stammt aus dem Zufall der Ziehung: Nur "
        f"{pct(share_between)} der Twin-Varianz unterscheidet die Twins voneinander (A2), ihre Erwartungswerte sind "
        f"enger als die Personen (2b). Nur {pct(v['Twin im Milieu seiner Person'])} der Twins landen im Milieu ihrer "
        "Person (2d), und die Werte der Twins sind stark demografisch sortiert (Fazit 3). Als Ersatz für die reale "
        "Wertestruktur taugt die synthetische Stichprobe damit nur in groben Zügen.",
        "3. **Was das Profil bringt:** Das volle Profil im Prompt bringt bei der Rangfolge der Werte etwas mehr als "
        "Geschlecht, Alter und Bildung, wenn man die Erwartungswerte des Twins nimmt, und etwas weniger, wenn man "
        "die gezogenen Antworten nimmt; beim Abstand zur Antwort bringt es in beiden Varianten weniger (1a, 1b). "
        "Ob die Anweisung gegen den Varianzkollaps die Twins weniger stereotyp macht, ist offen: Dafür fehlt der "
        "Vergleichslauf ohne diese Anweisung (DOKUMENTATION.md, Abschnitt 6).",
        "",
        "## Anhang",
        "",
        "### 1b′ Trennschärfe je Frage",
        fig("FF1b2_trennschaerfe"),
        "",
        desc(f"Gesichert besser als der Demografie-Mittelwert ist der Twin bei "
             f"{int(v['Items gesichert besser als Zellmittel (Bootstrap-KI der Differenz > 0)'])} von 21 Fragen, "
             f"gesichert schlechter bei {int(v['Items gesichert schlechter als Zellmittel'])} (Punktschätzer: besser "
             f"bei {n_items_better}, mit gezogenen Antworten bei {int(v['Items mit LLM-ρ gezogen > Zellmittel-ρ'])}). "
             "Praktisch gleichauf (Abstand < 0,01) liegen "
             + (", ".join(P.ITEM_SHORT[i] for i in close) if close else "keine Fragen")
             + f". Hier wird eine Frage über alle {n} Personen betrachtet, nicht eine Person über 21 Fragen; ein ρ "
             "von 0,3 ist ein schwacher Zusammenhang. Kräftig = 95-%-Intervall der Differenz Twin − "
             "Demografie-Mittelwert über 0 (gepaarter Bootstrap über Personen), schwarze Linie = Intervall des "
             "Twins, grauer Punkt = Demografie-Mittelwert; die Zahlen stehen in zwei Spalten rechts."),
        "",
        "### 1d Subgruppen",
        fig("FF1d_subgruppen"),
        "",
        desc("Jeder Balken ist der Fehler der Gruppe minus Gesamtfehler, die Zahl daneben der MAE der Gruppe; "
             "Signifikanz per ANOVA mit Holm-Korrektur über die Merkmale. Pink = ungenauer, grün = genauer, blass = "
             "nicht signifikant; die Achse reicht nur bis ±0,1."),
        "",
        "| Merkmal | η² | p (ANOVA, Holm) | p (Kruskal-Wallis) |",
        "|---|---|---|---|",
        *[f"| {r.merkmal} | {_de(r.eta2, 3)} | {_pval(r.p_holm)} | {_pval(r.kruskal_p)} |" for r in tests.itertuples()],
        "",
        "Die Unterschiede sind klein. In der multiplen Regression erklären alle Merkmale zusammen "
        f"R² = {_de(v['Regression MAE ~ Demografie R²'] * 100, 1)} % des Twin-MAE (signifikant nach Holm: "
        + (", ".join(coef[coef.p_holm < 0.05].term) or "keines") + ").",
        "",
        "### 1e Varianzkollaps innerhalb der Demografie",
        fig("FF1e_varianzkollaps"),
        "",
        desc(f"Die gezogenen Antworten streuen bei {int(v['Items mit LLM-SD über Bootstrap-97,5-%'])} von 21 Fragen "
             "stärker als bei Personen, die Erwartungswerte der Twins aber bei "
             f"{int(v['Items mit SD der LLM-Erwartungswerte unter Bootstrap-2,5-%'])} Fragen deutlich enger. Jeder "
             "Punkt ist die Standardabweichung der Antworten innerhalb gleicher Demografie (Geschlecht × Alter × "
             f"Bildung, {vk.attrs['n_zellen']} Zellen mit mindestens 20 Personen), gemittelt über die Zellen. Blau = "
             "Personen mit 95-%-Bootstrap-Band, Orange = Twins (voll = gezogen, Ring = Erwartungswert). A2 zeigt "
             "dieselbe Aussage über alle Personen."),
        "",
        f"Within-Cell-SD: Twins gezogen {_de(v['Within-Cell-SD LLM (Mittel Items)'])}, Personen "
        f"{_de(v['Within-Cell-SD Mensch (Mittel Items)'])}, Twin-Erwartungswerte "
        f"{_de(v['Within-Cell-SD LLM-Erwartungswerte (Mittel Items)'])}.",
        "",
        "### 2c Form",
        fig("FF2c_form"),
        "",
        desc(f"Nein (p ≤ {_de(g.loc['gesamt', 'mmd_p'], 3)}): Die Twin-Verteilungen sind breiter und bei Hedonismus "
             "und Leistung nach links, bei Konformität nach rechts verschoben. MMD vergleicht ganze Verteilungen ohne "
             "Annahme über ihre Form; im Permutationstest werden die Bezeichnungen Person/Twin 500-mal zufällig "
             "vertauscht. Bei N = 2 262 ist ein signifikanter Unterschied praktisch sicher; inhaltlich sagen 2a und "
             "2b dasselbe. X-Achse: zentrierte Wichtigkeit; gestrichelte Linien = Mittelwerte, Mischfarbe = "
             "Überlappung."),
        "",
        "### Sensitivitätsanalyse: Ebene 1 mit gezogenen Antworten",
        "",
        "Dieselben Rechnungen wie in 1a–1d, einmal mit den Erwartungswerten des Twins (Hauptergebnis) und einmal mit "
        "den gezogenen Antworten des Laufs; der fremde Twin wird jeweils aus derselben Variante gebildet, die "
        "Vergleichsgrößen aus den Antworten der Personen bleiben gleich. Die Spanne zeigt dieselbe Kennzahl über 20 "
        "neue Ziehungen aus denselben Wahrscheinlichkeiten, ohne neuen Modellaufruf: Sie trennt die Wirkung der Wahl "
        "Erwartungswert/Ziehung von der Wirkung der einen Ziehung des Laufs. Zur Laufvariabilität des Modells sagt sie "
        "nichts. Alle Werte: `sensitivitaet_ebene1.csv`, `sensitivitaet_aussagen.csv`.",
        "",
        "| Unterfrage | Kennzahl | Erwartungswert | gezogen | Spanne 20 neue Ziehungen |",
        "|---|---|---|---|---|",
        *[f"| {r.unterfrage} | {r.kennzahl} | {wert(r.erwartungswert, r.kennzahl)} | {wert(r.gezogen, r.kennzahl)} | "
          + ("–" if pd.isna(r.neuziehungen_min) else
             f"{wert(r.neuziehungen_min, r.kennzahl)} – {wert(r.neuziehungen_max, r.kennzahl)}") + " |"
          for r in sens.itertuples()],
        "",
        "**Welche Aussagen hängen von der Wahl ab?**",
        "",
        "| Unterfrage | Aussage | Erwartungswert | gezogen | gezogen, Anteil neuer Ziehungen | hängt ab |",
        "|---|---|---|---|---|---|",
        *[f"| {r.unterfrage} | {r.aussage} | {'ja' if r.erwartungswert else 'nein'} | "
          f"{'ja' if r.gezogen else 'nein'} | {pct(r.gezogen_anteil_neuziehungen)} | "
          f"{'**ja**' if r.haengt_von_wahl_ab else 'nein'} |" for r in aussagen.itertuples()],
        "",
        f"{n_dep} von {len(aussagen)} Aussagen hängen von der Wahl ab, und zwar in allen neuen Ziehungen gleich, "
        "also nicht wegen der einen Ziehung des Laufs. Betroffen ist nur der Vergleich mit dem Demografie-Mittelwert "
        "bei Rangfolge und Trennschärfe (1b, A3, 1b′): Mit Erwartungswerten liegt der Twin knapp vor dem "
        "Demografie-Mittelwert, mit gezogenen Antworten dahinter. Robust sind: Der Twin ist genauer als ein fremder "
        "Twin und enthält Information über die Person; er ist beim MAE schlechter als der Demografie-Mittelwert; "
        "seine Fehler sind überwiegend gerichtet (1c, der Mean Error ist in beiden Varianten in Erwartung gleich). "
        "Der Varianzkollaps (1e, A2) wird ohnehin in beiden Varianten berichtet, weil dort der Unterschied selbst "
        "der Befund ist. Der Vergleich mit gezogenen Antworten ist asymmetrisch: Nur der Twin trägt das Rauschen "
        "einer Ziehung, die Vergleichsgrößen sind Mittelwerte. Der Erwartungswert ist die passende Punktprognose, "
        "sofern die verbalisierten Wahrscheinlichkeiten halbwegs kalibriert sind (DOKUMENTATION.md, 5.3).",
    ]
    (out / "report.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def subgroup_stats(twins: pd.DataFrame, demo: pd.DataFrame) -> dict:
    groups, tests = [], []
    mae = twins["mae"].to_numpy()
    for var in demo.columns:
        lab = demo[var]
        samples = []
        order = sorted(lab.dropna().unique()) if var == "Werte-Milieu" else _group_order(lab)
        for g in order:
            sel = (lab == g).to_numpy()
            m, hw = _ci_mean(mae[sel])
            groups.append({"merkmal": var, "gruppe": g, "n": int(sel.sum()), "mae": m, "ci": hw})
            samples.append(mae[sel])
        all_x = np.concatenate(samples)
        ss_b = sum(len(s) * (s.mean() - all_x.mean()) ** 2 for s in samples)
        tests.append({"merkmal": var, "anova_p": stats.f_oneway(*samples).pvalue,
                      "kruskal_p": stats.kruskal(*samples).pvalue,
                      "eta2": ss_b / ((all_x - all_x.mean()) ** 2).sum()})
    tests = pd.DataFrame(tests)
    tests["p_holm"] = ebene1.holm(tests["anova_p"].to_numpy())
    return {"gruppen": pd.DataFrame(groups), "tests": tests}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    print(run(a.run_dir, a.seed))


if __name__ == "__main__":
    main()
