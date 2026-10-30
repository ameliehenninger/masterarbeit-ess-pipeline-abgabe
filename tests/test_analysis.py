"""Tests für Phase 4 (Auswertung Ebene 1 und 2) – Metriken gegen bekannte Werte und Referenzimplementierungen."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from ess_pipeline.analysis import ebene1, ebene2
from ess_pipeline.analysis.data import BASIC_VALUES, SUBGROUPS, Twins
from ess_pipeline.config import PVQ_ITEMS


def _twins(n: int = 120, noise: float = 1.0, seed: int = 0) -> Twins:
    rng = np.random.default_rng(seed)
    h = rng.integers(1, 7, size=(n, 21))
    lm = np.clip(h + np.round(rng.normal(0, noise, size=h.shape)), 1, 6).astype(int)
    ids = [f"P{i}" for i in range(n)]
    hum = pd.DataFrame(h, index=ids, columns=PVQ_ITEMS)
    llm = pd.DataFrame(lm, index=ids, columns=PVQ_ITEMS)
    sc = lambda df: pd.DataFrame(rng.normal(size=(n, 10)), index=ids, columns=BASIC_VALUES)  # noqa: E731
    demo = pd.DataFrame({v: rng.choice(["a", "b"], size=n) for v in SUBGROUPS}, index=ids)
    return Twins(ids, hum, llm, sc(hum), sc(llm), demo, {it: i + 1 for i, it in enumerate(PVQ_ITEMS)})


def test_rowwise_spearman_matches_scipy():
    rng = np.random.default_rng(1)
    a, b = rng.integers(1, 7, (30, 21)), rng.integers(1, 7, (30, 21))
    got = ebene1.rowwise_spearman(a, b)
    ref = [stats.spearmanr(x, y).statistic for x, y in zip(a, b, strict=True)]
    np.testing.assert_allclose(got, ref)
    assert np.isnan(ebene1.rowwise_spearman(np.full((1, 21), 3), b[:1]))[0]


def test_holm():
    np.testing.assert_allclose(ebene1.holm(np.array([0.01, 0.04, 0.03])), [0.03, 0.06, 0.06])


def test_perfect_twins_have_zero_error():
    t = _twins(noise=0)
    tw = ebene1.twin_table(t)
    assert (tw["mae"] == 0).all() and (tw["me"] == 0).all()
    assert np.allclose(tw["spearman"].dropna(), 1)


def test_shuffle_never_keeps_own_row():
    rng = np.random.default_rng(3)
    x = np.arange(50)[:, None]
    for _ in range(20):
        assert (ebene1._shuffled(x, rng)[:, 0] != np.arange(50)).all()


def test_twins_beat_shuffle_when_llm_is_informative():
    t = _twins(noise=0.7)
    base = ebene1.baselines(t, seed=1)
    tw = ebene1.twin_table(t)
    assert tw["mae"].mean() < base["shuffle_mae"]
    assert tw["spearman"].mean() > base["shuffle_spearman"]


def test_item_table_and_confusion():
    t = _twins()
    base = ebene1.baselines(t, seed=1)
    items = ebene1.item_table(t, base)
    assert len(items) == 21 and items["frage"].tolist() == [f"Q{i}" for i in range(1, 22)]
    assert ebene1.confusion(t).to_numpy().sum() == 120 * 21


def test_subgroup_eta2_between_0_and_1():
    t = _twins()
    groups, tests = ebene1.subgroup_tables(t, ebene1.twin_table(t))
    assert ((tests["eta2"] >= 0) & (tests["eta2"] <= 1)).all()
    assert groups.groupby("merkmal")["n"].sum().eq(120).all()


def test_bures_wasserstein():
    a = np.diag([4.0, 1.0])
    assert ebene2.bures_wasserstein(a, a) == pytest.approx(0, abs=1e-9)
    # kommutierende Matrizen: d² = Σ (√a_i − √b_i)²
    assert ebene2.bures_wasserstein(a, np.diag([1.0, 1.0])) == pytest.approx(1.0)


def test_mmd_detects_shift_but_not_same_distribution():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(150, 3))
    same, p_same, _ = ebene2.mmd_test(x, rng.normal(size=(150, 3)), rng, n_perm=200)
    shift, p_shift, _ = ebene2.mmd_test(x, rng.normal(1, 1, size=(150, 3)), rng, n_perm=200)
    assert shift > same and p_shift < 0.01 and p_same > 0.01


def test_cluster_matching_recovers_identical_structure():
    rng = np.random.default_rng(0)
    centers = np.array([[3, 0, 0, 0, 0, 0, 0, 0, 0, 0], [-3, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                        [0, 3, 0, 0, 0, 0, 0, 0, 0, 0]], float)
    lab = rng.integers(0, 3, 150)
    xh = centers[lab] + rng.normal(0, 0.3, (150, 10))
    t = _twins(n=150)
    t.human_scores[:] = xh
    t.llm_scores[:] = xh + rng.normal(0, 0.05, xh.shape)
    res = ebene2.run(t, k=3, n_perm=50)
    assert res.summary["ari_eigenes_clustering"] == pytest.approx(1)
    assert res.summary["ari_menschliche_zentroide"] == pytest.approx(1)
    assert np.allclose(res.centers_h, res.centers_l, atol=0.1)


# ---------------------------------------------------------------------------
# Auswertung entlang der Forschungsfragen (analysis/forschungsfragen.py)
# ---------------------------------------------------------------------------

def test_uniform_mae_is_exact_expectation():
    from ess_pipeline.analysis import forschungsfragen as ff

    h = np.array([[1] * 21, [3] * 21], float)
    # |1 − k| über k = 1…6: (0+1+2+3+4+5)/6 = 2,5;  |3 − k|: (2+1+0+1+2+3)/6 = 1,5
    np.testing.assert_allclose(ff.uniform_mae(h), [2.5, 1.5])


def test_cell_mean_profile_leaves_person_out():
    from ess_pipeline.analysis import forschungsfragen as ff

    t = _twins(n=60, seed=5)
    h, cp = t.items("human"), ff.cell_mean_profile(t)
    lab = ff.cell_labels(t).to_numpy()
    for i in (0, 17, 42):
        others = (lab == lab[i]) & (np.arange(len(lab)) != i)
        np.testing.assert_allclose(cp[i], h[others].mean(axis=0))


def test_deviation_spearman_removes_population_profile():
    from ess_pipeline.analysis import forschungsfragen as ff

    t = _twins(noise=0)
    h = t.items("human")
    assert np.allclose(ff.deviation_spearman(h, h), 1)
    # Alle Twins geben dasselbe Profil: kein persönlicher Anteil, Abweichungs-ρ undefiniert
    same = np.tile(np.arange(1, 22, dtype=float) % 6 + 1, (len(h), 1))
    assert np.isnan(ff.deviation_spearman(h, same)).all()
