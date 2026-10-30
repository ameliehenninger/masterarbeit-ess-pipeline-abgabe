"""
Ebene 2 – Segment- und Cluster-Ebene: bildet die simulierte Population dieselben Werte-Milieus?

Vorgehen:

1. Merkmalsraum: standardmäßig die 10 MRAT-zentrierten Schwartz-Basiswerte (Werteprofil ohne Antwortstil);
   alternativ die 21 umgepolten Items (`space="items"`, dann zählt der Antwortstil mit).
2. k-Means getrennt für Menschen und LLM, mit gleichem k. k wird über den Silhouettenkoeffizienten der
   *menschlichen* Daten gewählt (oder fest vorgegeben).
3. LLM-Cluster den menschlichen Clustern zuordnen: Hungarian-Verfahren auf den Zentroid-Abständen.

Vier Kategorien (DOKUMENTATION.md, Abschnitt 5.1), je Clusterpaar und für die ganze Population:

1. Lage        – euklidischer Abstand der Zentroide
2. Streuung    – Gesamtstreuung tr(Σ) je Seite und Bures-Wasserstein-Distanz der Kovarianzmatrizen
3. Form        – Maximum Mean Discrepancy (RBF-Kern, Median-Heuristik) mit Permutationstest
4. Zuordnung   – Adjusted Rand Index der Twins: (a) zwei eigenständige Clusterings,
                 (b) LLM-Antworten den menschlichen Zentroiden zugeordnet

Vergleichsmaßstab für 1–3: dieselben Kennzahlen zwischen zwei zufälligen Hälften der *menschlichen* Daten
(Split-Half). Das ist der Abstand, den allein der Stichprobenzufall erzeugt.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from ..config import PVQ_ITEMS
from .data import BASIC_VALUES, Twins

K_MAX = 8
MIN_PER_CLUSTER = 10   # k höchstens n / 10, sonst sind die Cluster zu klein für Kovarianzen und MMD
N_INIT = 50
N_PERM = 500
N_SPLIT = 20
SILHOUETTE_SAMPLE = None  # alle Punkte (n ≈ 2 300 ist schnell genug)


# ---------------------------------------------------------------------------
# Distanzen zwischen Verteilungen
# ---------------------------------------------------------------------------

def psd_sqrt(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eigh((a + a.T) / 2)
    return (v * np.sqrt(np.clip(w, 0, None))) @ v.T


def bures_wasserstein(a: np.ndarray, b: np.ndarray) -> float:
    """d(A,B)² = tr A + tr B − 2 tr (A^½ B A^½)^½  (= W2 zwischen zentrierten Normalverteilungen)."""
    ra = psd_sqrt(a)
    cross = psd_sqrt(ra @ b @ ra)
    return float(np.sqrt(max(np.trace(a) + np.trace(b) - 2 * np.trace(cross), 0.0)))


def _sq_dists(z: np.ndarray) -> np.ndarray:
    n2 = (z**2).sum(axis=1)
    return np.maximum(n2[:, None] + n2[None, :] - 2 * z @ z.T, 0)


def mmd_test(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, n_perm: int = N_PERM,
             bandwidth: float | None = None) -> tuple[float, float, float]:
    """
    Unverzerrtes MMD² mit RBF-Kern k(a,b) = exp(−‖a−b‖² / (2σ²)), σ = Median der paarweisen Abstände
    (gepoolt), und Permutations-p-Wert. Rückgabe: (MMD², p, σ).
    """
    z = np.vstack([x, y]).astype(np.float64)
    n, m = len(x), len(y)
    d2 = _sq_dists(z)
    if bandwidth is None:
        iu = np.triu_indices(len(z), 1)
        bandwidth = float(np.sqrt(np.median(d2[iu])))
    kmat = np.exp(-d2 / (2 * bandwidth**2)).astype(np.float32)
    del d2

    def stat(member: np.ndarray) -> np.ndarray:
        """member: (N, P) 0/1-Matrix, 1 = Gruppe X. Gibt MMD² je Spalte."""
        u = member.astype(np.float32)
        v = 1 - u
        ku, kv = kmat @ u, kmat @ v
        sxx = (u * ku).sum(axis=0) - n          # Diagonale (k = 1) herausnehmen
        syy = (v * kv).sum(axis=0) - m
        sxy = (u * kv).sum(axis=0)
        return sxx / (n * (n - 1)) + syy / (m * (m - 1)) - 2 * sxy / (n * m)

    obs = np.zeros((n + m, 1))
    obs[:n] = 1
    observed = float(stat(obs)[0])
    if n_perm <= 0:
        return observed, np.nan, bandwidth
    perms = np.zeros((n + m, n_perm))
    for j in range(n_perm):
        perms[rng.permutation(n + m)[:n], j] = 1
    null = stat(perms)
    p = (1 + np.sum(null >= observed)) / (1 + n_perm)
    return observed, float(p), bandwidth


def compare(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, n_perm: int = N_PERM) -> dict:
    """Die drei Verteilungsvergleiche (Lage, Streuung, Form) zwischen zwei Punktwolken."""
    cx, cy = np.cov(x, rowvar=False), np.cov(y, rowvar=False)
    mmd2, p, sigma = mmd_test(x, y, rng, n_perm)
    return {
        "zentroid_abstand": float(np.linalg.norm(x.mean(axis=0) - y.mean(axis=0))),
        "streuung_mensch": float(np.trace(cx)), "streuung_llm": float(np.trace(cy)),
        "streuung_verhaeltnis": float(np.trace(cy) / np.trace(cx)) if np.trace(cx) > 0 else np.nan,
        "bures_wasserstein": bures_wasserstein(cx, cy),
        "mmd2": mmd2, "mmd_p": p, "mmd_sigma": sigma,
    }


def split_half(x: np.ndarray, rng: np.random.Generator, reps: int = N_SPLIT) -> dict:
    """Rauschniveau: dieselben Kennzahlen zwischen zwei zufälligen Hälften derselben menschlichen Daten."""
    out = []
    for _ in range(reps):
        idx = rng.permutation(len(x))
        a, b = x[idx[: len(x) // 2]], x[idx[len(x) // 2:]]
        out.append({
            "zentroid_abstand": np.linalg.norm(a.mean(axis=0) - b.mean(axis=0)),
            "bures_wasserstein": bures_wasserstein(np.cov(a, rowvar=False), np.cov(b, rowvar=False)),
            "mmd2": mmd_test(a, b, rng, n_perm=0)[0],
        })
    return {f"ref_{k}": float(np.mean([o[k] for o in out])) for k in out[0]}


# ---------------------------------------------------------------------------
# Clustering
# ---------------------------------------------------------------------------

def features(t: Twins, space: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    if space == "werte":
        return t.human_scores[BASIC_VALUES].to_numpy(float), t.llm_scores[BASIC_VALUES].to_numpy(float), BASIC_VALUES
    if space == "items":
        return t.items("human"), t.items("llm"), PVQ_ITEMS
    raise ValueError(f"Unbekannter Merkmalsraum {space!r} (werte | items)")


def kmeans(x: np.ndarray, k: int, seed: int) -> KMeans:
    return KMeans(n_clusters=k, n_init=N_INIT, random_state=seed).fit(x)


def k_range(n: int) -> range:
    return range(2, min(K_MAX, n // MIN_PER_CLUSTER) + 1)


def k_selection(xh: np.ndarray, xl: np.ndarray, seed: int) -> pd.DataFrame:
    rows = []
    for k in k_range(len(xh)):
        for who, x in (("mensch", xh), ("llm", xl)):
            km = kmeans(x, k, seed)
            rows.append({"k": k, "daten": who, "silhouette": silhouette_score(x, km.labels_),
                         "inertia": km.inertia_})
    return pd.DataFrame(rows)


def match(ch: np.ndarray, cl: np.ndarray) -> np.ndarray:
    """perm[c] = Index des LLM-Clusters, der zum menschlichen Cluster c gehört (minimale Zentroid-Abstände)."""
    cost = np.linalg.norm(ch[:, None, :] - cl[None, :, :], axis=2)
    rows, cols = linear_sum_assignment(cost)
    perm = np.empty(len(ch), int)
    perm[rows] = cols
    return perm


@dataclass
class ClusterResult:
    space: str
    feature_names: list[str]
    k: int
    k_table: pd.DataFrame
    xh: np.ndarray
    xl: np.ndarray
    labels_h: np.ndarray            # menschliches Clustering
    labels_l: np.ndarray            # LLM-Clustering, umbenannt auf die passenden menschlichen Cluster
    labels_l_proj: np.ndarray       # LLM-Punkte dem nächsten menschlichen Zentroid zugeordnet
    centers_h: np.ndarray
    centers_l: np.ndarray           # in derselben Reihenfolge wie centers_h
    metrics: pd.DataFrame           # eine Zeile je Clusterpaar + "gesamt"
    summary: dict


def run(t: Twins, space: str = "werte", k: int | None = None, seed: int = 42,
        n_perm: int = N_PERM) -> ClusterResult | None:
    """None, wenn zu wenige Twins für ein Clustering vorliegen (weniger als 2 · MIN_PER_CLUSTER)."""
    xh, xl, names = features(t, space)
    if len(k_range(len(xh))) == 0 and k is None:
        return None
    k_table = k_selection(xh, xl, seed)
    if k is None:
        hum = k_table[k_table["daten"] == "mensch"]
        k = int(hum.loc[hum["silhouette"].idxmax(), "k"])

    kh, kl = kmeans(xh, k, seed), kmeans(xl, k, seed)
    perm = match(kh.cluster_centers_, kl.cluster_centers_)
    inv = np.argsort(perm)                     # LLM-Cluster j -> menschlicher Cluster inv[j]
    labels_h = kh.labels_
    labels_l = inv[kl.labels_]
    centers_l = kl.cluster_centers_[perm]
    labels_l_proj = kh.predict(xl)

    rng = np.random.default_rng(seed)
    rows = [{"cluster": "gesamt", "n_mensch": len(xh), "n_llm": len(xl), **compare(xh, xl, rng, n_perm),
             **split_half(xh, rng)}]
    for c in range(k):
        a, b = xh[labels_h == c], xl[labels_l == c]
        row = {"cluster": c + 1, "n_mensch": len(a), "n_llm": len(b)}
        if len(a) > 2 and len(b) > 2:
            row |= compare(a, b, rng, n_perm) | split_half(a, rng)
        rows.append(row)
    metrics = pd.DataFrame(rows)
    metrics["anteil_mensch"] = metrics["n_mensch"] / len(xh)
    metrics["anteil_llm"] = metrics["n_llm"] / len(xl)
    # Abstand der menschlichen Zentroide untereinander: wie weit liegen die Milieus selbst auseinander?
    between = np.linalg.norm(kh.cluster_centers_[:, None] - kh.cluster_centers_[None], axis=2)
    summary = {
        "raum": space, "k": k,
        "silhouette_mensch": float(silhouette_score(xh, labels_h)),
        "silhouette_llm": float(silhouette_score(xl, kl.labels_)),
        "ari_eigenes_clustering": float(adjusted_rand_score(labels_h, labels_l)),
        "ari_menschliche_zentroide": float(adjusted_rand_score(labels_h, labels_l_proj)),
        "gleicher_cluster_eigen": float((labels_h == labels_l).mean()),
        "gleicher_cluster_projiziert": float((labels_h == labels_l_proj).mean()),
        "zufall_gleicher_cluster": float(np.sum(np.bincount(labels_h, minlength=k) / len(xh)
                                                * np.bincount(labels_l_proj, minlength=k) / len(xl))),
        "abstand_menschliche_zentroide_mittel": float(between[np.triu_indices(k, 1)].mean()) if k > 1 else np.nan,
    }
    g = metrics.iloc[0]
    summary |= {f"gesamt_{c}": g[c] for c in ["zentroid_abstand", "streuung_mensch", "streuung_llm",
                                             "streuung_verhaeltnis", "bures_wasserstein", "mmd2", "mmd_p",
                                             "ref_zentroid_abstand", "ref_bures_wasserstein", "ref_mmd2"]}
    return ClusterResult(space, names, k, k_table, xh, xl, labels_h, labels_l, labels_l_proj,
                         kh.cluster_centers_, centers_l, metrics, summary)


def contingency(a: np.ndarray, b: np.ndarray, k: int) -> np.ndarray:
    m = np.zeros((k, k), int)
    np.add.at(m, (a, b), 1)
    return m
