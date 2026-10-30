"""
Ebene 1 – Twin-Ebene: jede simulierte Person gegen ihr echtes Vorbild, Item für Item.

Vier Kategorien (DOKUMENTATION.md, Abschnitt 5.1):

1. Absolute Genauigkeit   – MAE (dazu RMSE, bestraft große Ausreißer stärker)
2. Profilähnlichkeit      – Spearman-Rangkorrelation über die 21 Items je Twin-Paar
3. Systematischer Bias    – Mean Error (LLM − Mensch) je Item, t-Test gegen 0 mit Holm-Korrektur
4. Subgruppen             – MAE je demografischer Gruppe, ANOVA (und Kruskal-Wallis als robuste Prüfung)

Damit die Zahlen einordbar sind, gibt es zwei Vergleichsgrößen ohne Personenwissen:

- Zufallspaarung: LLM-Antworten einer *anderen* Person (Zeilen gemischt). Zeigt, wie viel Genauigkeit
  allein daher kommt, dass das LLM typische Antworten der Population trifft.
- Mittelprofil: für jede Person die mittlere Antwort aller echten Personen je Item (ganze ESS-Stichprobe).

Alle Items sind umgepolt (6 = sehr wichtig); Fehler = LLM − Mensch.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..config import PVQ_ITEMS
from .data import ITEM_VALUE, SUBGROUPS, Twins

N_SHUFFLE = 20
MIN_GROUP_N = 2   # kleinere Gruppen werden berichtet, aber nicht getestet


# ---------------------------------------------------------------------------
# Bausteine
# ---------------------------------------------------------------------------

def rowwise_spearman(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Spearman je Zeile (Bindungen mit Durchschnittsrängen); NaN, wenn eine Zeile konstant ist."""
    ra = stats.rankdata(a, axis=1)
    rb = stats.rankdata(b, axis=1)
    ra = ra - ra.mean(axis=1, keepdims=True)
    rb = rb - rb.mean(axis=1, keepdims=True)
    den = np.sqrt((ra**2).sum(axis=1) * (rb**2).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (ra * rb).sum(axis=1) / den, np.nan)


def holm(p: np.ndarray) -> np.ndarray:
    """Holm-Bonferroni-adjustierte p-Werte."""
    p = np.asarray(p, float)
    order = np.argsort(p)
    adj = np.minimum(1, (len(p) - np.arange(len(p))) * p[order])
    adj = np.maximum.accumulate(adj)
    out = np.empty_like(adj)
    out[order] = adj
    return out


def mean_ci(x: np.ndarray, level: float = 0.95) -> tuple[float, float, float]:
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    m = x.mean()
    if len(x) < 2:
        return m, np.nan, np.nan
    h = stats.t.ppf((1 + level) / 2, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return m, m - h, m + h


def _shuffled(llm: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Zeilen so mischen, dass keine Person ihre eigenen LLM-Antworten behält."""
    n = len(llm)
    perm = rng.permutation(n)
    fixed = np.flatnonzero(perm == np.arange(n))
    for i in fixed:  # jeden Fixpunkt mit einem zufälligen anderen Platz tauschen
        j = (i + 1 + rng.integers(n - 1)) % n
        perm[i], perm[j] = perm[j], perm[i]
    return llm[perm]


# ---------------------------------------------------------------------------
# Kennzahlen
# ---------------------------------------------------------------------------

def twin_table(t: Twins) -> pd.DataFrame:
    """Eine Zeile je Twin-Paar."""
    h, lm = t.items("human"), t.items("llm")
    e = lm - h
    return pd.DataFrame({
        "mae": np.abs(e).mean(axis=1),
        "rmse": np.sqrt((e**2).mean(axis=1)),
        "me": e.mean(axis=1),
        "spearman": rowwise_spearman(h, lm),
        "exakt": (e == 0).mean(axis=1),
        "sd_mensch": h.std(axis=1, ddof=1),
        "sd_llm": lm.std(axis=1, ddof=1),
    }, index=pd.Index(t.ids, name="id"))


def baselines(t: Twins, seed: int, n_shuffle: int = N_SHUFFLE) -> dict:
    h, lm = t.items("human"), t.items("llm")
    rng = np.random.default_rng(seed)
    mae_s, rmse_s, rho_s, item_mae_s = [], [], [], []
    for _ in range(n_shuffle):
        ls = _shuffled(lm, rng)
        e = ls - h
        mae_s.append(np.abs(e).mean(axis=1))
        rmse_s.append(np.sqrt((e**2).mean(axis=1)))
        rho_s.append(rowwise_spearman(h, ls))
        item_mae_s.append(np.abs(e).mean(axis=0))
    # Mittelprofil aus der ganzen ESS-Stichprobe, nicht nur aus den Personen dieses Laufs
    pop = t.population_mean if t.population_mean is not None else h.mean(axis=0)
    mean_profile = np.broadcast_to(pop, h.shape)
    e_mp = mean_profile - h
    return {
        "shuffle_mae_twin": np.concatenate(mae_s),      # Verteilung über alle Wiederholungen
        "shuffle_rho_twin": np.concatenate(rho_s),
        "shuffle_mae": float(np.mean(mae_s)),
        "shuffle_rmse": float(np.mean(rmse_s)),
        "shuffle_spearman": float(np.nanmean(rho_s)),
        "shuffle_item_mae": np.mean(item_mae_s, axis=0),
        "mittelprofil_mae": float(np.abs(e_mp).mean()),
        "mittelprofil_rmse": float(np.sqrt((e_mp**2).mean(axis=1)).mean()),
        "mittelprofil_spearman": float(np.nanmean(rowwise_spearman(h, mean_profile))),
        "mittelprofil_item_mae": np.abs(e_mp).mean(axis=0),
    }


def item_table(t: Twins, base: dict) -> pd.DataFrame:
    """Eine Zeile je Item (Fragebogenreihenfolge): Genauigkeit und Richtung des Fehlers."""
    h, lm = t.items("human"), t.items("llm")
    e = lm - h
    res = stats.ttest_1samp(e, 0.0, axis=0)
    rows = []
    for j, item in enumerate(PVQ_ITEMS):
        m, lo, hi = mean_ci(e[:, j])
        sd = e[:, j].std(ddof=1)
        rows.append({
            "frage": f"Q{t.question_no[item]}", "item": item, "wert": ITEM_VALUE[item],
            "mittel_mensch": h[:, j].mean(), "mittel_llm": lm[:, j].mean(),
            "sd_mensch": h[:, j].std(ddof=1), "sd_llm": lm[:, j].std(ddof=1),
            "mae": np.abs(e[:, j]).mean(), "rmse": np.sqrt((e[:, j] ** 2).mean()),
            "me": m, "me_ci_unten": lo, "me_ci_oben": hi,
            "cohens_d": m / sd if sd > 0 else np.nan,
            "t": res.statistic[j], "p": res.pvalue[j],
            "exakt": (e[:, j] == 0).mean(),
            "spearman_item": stats.spearmanr(h[:, j], lm[:, j]).statistic,
            "mae_zufallspaarung": base["shuffle_item_mae"][j],
            "mae_mittelprofil": base["mittelprofil_item_mae"][j],
        })
    df = pd.DataFrame(rows)
    df["p_holm"] = holm(df["p"].to_numpy())
    df["signifikant"] = df["p_holm"] < 0.05
    # Reihenfolge wie im Fragebogen (Q1 … Q21)
    return df.sort_values("frage", key=lambda s: s.str[1:].astype(int)).reset_index(drop=True)


def confusion(t: Twins) -> pd.DataFrame:
    """Kreuztabelle echte Antwort (Zeilen) × LLM-Antwort (Spalten), umgepolte Skala 1–6."""
    h = t.items("human").ravel().astype(int)
    lm = t.items("llm").ravel().astype(int)
    m = np.zeros((6, 6), int)
    np.add.at(m, (h - 1, lm - 1), 1)
    k = range(1, 7)
    return pd.DataFrame(m, index=pd.Index(k, name="mensch"), columns=pd.Index(k, name="llm"))


def subgroup_tables(t: Twins, twins: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    (gruppen, tests): je Merkmal und Gruppe MAE/ME/Spearman mit 95-%-KI;
    je Merkmal ANOVA und Kruskal-Wallis auf dem Twin-MAE, Effektstärke η².
    """
    groups, tests = [], []
    for var in SUBGROUPS:
        lab = t.demo[var]
        samples = []
        for g in _group_order(lab):
            sel = (lab == g).to_numpy()
            x = twins["mae"].to_numpy()[sel]
            m, lo, hi = mean_ci(x)
            groups.append({
                "merkmal": var, "gruppe": g, "n": int(sel.sum()), "mae": m, "mae_ci_unten": lo, "mae_ci_oben": hi,
                "mae_sd": x.std(ddof=1) if len(x) > 1 else np.nan, "me": twins["me"].to_numpy()[sel].mean(),
                "spearman": np.nanmean(twins["spearman"].to_numpy()[sel]),
                "sd_mensch": twins["sd_mensch"].to_numpy()[sel].mean(),
            })
            samples.append(x)
        # getestet werden nur Gruppen mit mindestens MIN_GROUP_N Twins (bei kleinen Läufen evtl. keine)
        samples = [s for s in samples if len(s) >= MIN_GROUP_N]
        row = {"merkmal": var, "gruppen": len(samples), "n": int(sum(len(s) for s in samples)),
               "n_fehlend": int(lab.isna().sum()), "anova_f": np.nan, "anova_p": np.nan, "kruskal_h": np.nan,
               "kruskal_p": np.nan, "eta2": np.nan, "mae_spanne": np.nan}
        if len(samples) >= 2:
            all_x = np.concatenate(samples)
            ss_b = sum(len(s) * (s.mean() - all_x.mean()) ** 2 for s in samples)
            ss_t = ((all_x - all_x.mean()) ** 2).sum()
            f = stats.f_oneway(*samples)
            kw = stats.kruskal(*samples) if np.ptp(all_x) > 0 else None
            row |= {"anova_f": f.statistic, "anova_p": f.pvalue,
                    "kruskal_h": kw.statistic if kw else np.nan, "kruskal_p": kw.pvalue if kw else np.nan,
                    "eta2": ss_b / ss_t if ss_t > 0 else np.nan,
                    "mae_spanne": max(s.mean() for s in samples) - min(s.mean() for s in samples)}
        tests.append(row)
    tests = pd.DataFrame(tests)
    ok = tests["anova_p"].notna().to_numpy()
    tests["anova_p_holm"] = np.nan
    if ok.any():
        tests.loc[ok, "anova_p_holm"] = holm(tests.loc[ok, "anova_p"].to_numpy())
    return pd.DataFrame(groups), tests


def subgroup_items(t: Twins) -> pd.DataFrame:
    """ME und MAE je Item und Subgruppe (für die Heatmap „wo irrt das LLM bei wem“)."""
    e = t.items("llm") - t.items("human")
    rows = []
    for var in SUBGROUPS:
        lab = t.demo[var]
        for g in _group_order(lab):
            sel = (lab == g).to_numpy()
            for j, item in enumerate(PVQ_ITEMS):
                rows.append({"merkmal": var, "gruppe": g, "item": item, "wert": ITEM_VALUE[item],
                             "n": int(sel.sum()), "me": e[sel, j].mean(), "mae": np.abs(e[sel, j]).mean()})
    return pd.DataFrame(rows)


def _group_order(lab: pd.Series) -> list[str]:
    cats = [c for c in lab.dropna().unique()]
    # Altersgruppen und Bildungsstufen in natürlicher Reihenfolge, sonst nach Häufigkeit
    natural = ["15–29", "30–44", "45–59", "60–74", "75+", "niedrig", "mittel", "hoch",
               "Großstadt", "Kleinstadt", "ländlich"]
    if all(c in natural for c in cats):
        return sorted(cats, key=natural.index)
    return list(lab.value_counts().index)


def summary(twins: pd.DataFrame, items: pd.DataFrame, base: dict, tests: pd.DataFrame) -> dict:
    rho = twins["spearman"]
    return {
        "twins": len(twins),
        "mae": twins["mae"].mean(), "rmse": twins["rmse"].mean(), "me": twins["me"].mean(),
        "exakt": twins["exakt"].mean(),
        "spearman_mittel": rho.mean(), "spearman_median": rho.median(), "spearman_nan": int(rho.isna().sum()),
        "anteil_spearman_positiv": float((rho > 0).mean()),
        "zufallspaarung_mae": base["shuffle_mae"], "zufallspaarung_rmse": base["shuffle_rmse"],
        "zufallspaarung_spearman": base["shuffle_spearman"],
        "mittelprofil_mae": base["mittelprofil_mae"], "mittelprofil_rmse": base["mittelprofil_rmse"],
        "mittelprofil_spearman": base["mittelprofil_spearman"],
        "items_bias_signifikant": int(items["signifikant"].sum()),
        "subgruppen_signifikant": int((tests["anova_p_holm"] < 0.05).sum()),
    }
