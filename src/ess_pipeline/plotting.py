"""
Phase 2 – Visualisierung der ESS-Scores (ess_scores.csv) in drei Abbildungen:

1. plot1_basiswerte      – Verteilung der 10 Schwartz-Basiswerte (Kreisordnung)
2. plot2_higher_order    – Verteilung der 4 Higher-Order Values + die zwei
                           bipolaren Gegensatzpaare als Streudiagramm
3. plot3_wertekreis_xy   – Personen in der 2D-Ebene (x = SELFTRANS − SELFENH,
                           y = OPEN − CONS) mit Randverteilungen

Ausgabe: je Abbildung ein PNG im übergebenen Ordner (Standard: results/mensch/figures/).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # ohne Bildschirm lauffähig
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# Farben je Higher-Order Value (feste Reihenfolge, Default-Palette)
HOV_COLOR = {
    "OPEN": "#2a78d6",       # blau
    "SELFENH": "#eb6834",    # orange
    "CONS": "#1baf7a",       # aqua
    "SELFTRANS": "#6250d6",  # violett
}
HOV_LABEL = {
    "OPEN": "Offenheit für Wandel",
    "SELFENH": "Selbststärkung",
    "CONS": "Bewahrung",
    "SELFTRANS": "Selbsttranszendenz",
}
# Basiswerte in Schwartz' Kreisordnung, mit Zuordnung zum Higher-Order Value
BASIC = [
    ("SD", "Selbst-\nbestimmung", "OPEN"),
    ("ST", "Stimulation", "OPEN"),
    ("HE", "Hedonismus", "OPEN"),
    ("AC", "Leistung", "SELFENH"),
    ("PO", "Macht", "SELFENH"),
    ("SE", "Sicherheit", "CONS"),
    ("CO", "Konformität", "CONS"),
    ("TR", "Tradition", "CONS"),
    ("BE", "Wohlwollen", "SELFTRANS"),
    ("UN", "Universalis-\nmus", "SELFTRANS"),
]
HOV_ORDER = ["OPEN", "SELFENH", "CONS", "SELFTRANS"]
# Bis zu dieser Personenzahl werden die Einzelwerte als Punkte gezeigt
SHOW_POINTS_MAX_N = 50

INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": INK_2,
    "axes.labelcolor": INK,
    "axes.titlecolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})


def _save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def _zero_line(ax: plt.Axes, label: str | None = None) -> None:
    ax.axhline(0, color=INK_2, lw=1, ls="--", zorder=1)
    if label:
        ax.text(1.0, 0, f" {label}", transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=8, color=INK_2)


def _violins(ax: plt.Axes, data: list[np.ndarray], colors: list[str]) -> None:
    """Violine (Verteilung) + Box (IQR) + Median-Punkt + Mittelwert-Strich."""
    pos = np.arange(1, len(data) + 1)
    # Dichteschätzung nur, wenn die Werte streuen (bei wenigen LLM-Personen evtl. nicht)
    kde = [i for i, d in enumerate(data) if len(d) > 1 and np.ptp(d) > 0]
    if kde:
        parts = ax.violinplot([data[i] for i in kde], positions=pos[kde], widths=0.8,
                              showextrema=False, bw_method=0.25)
        for body, i in zip(parts["bodies"], kde, strict=True):
            body.set_facecolor(colors[i])
            body.set_edgecolor("white")
            body.set_linewidth(1)
            body.set_alpha(0.55)
            body.set_zorder(2)
    for p, d, c in zip(pos, data, colors, strict=True):
        if len(d) <= SHOW_POINTS_MAX_N:
            ax.scatter(np.full(len(d), p), d, s=14, color=c, alpha=0.8, lw=0, zorder=3)
        q1, med, q3 = np.percentile(d, [25, 50, 75])
        ax.vlines(p, q1, q3, color=c, lw=5, zorder=3)
        ax.scatter(p, med, s=28, color="white", edgecolor=c, lw=1.5, zorder=4)
        ax.hlines(d.mean(), p - 0.22, p + 0.22, color=INK, lw=1.5, zorder=4)
    ax.set_xlim(0.4, len(data) + 0.6)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def _legend_hov(ax: plt.Axes, **kw) -> None:
    handles = [plt.Rectangle((0, 0), 1, 1, color=HOV_COLOR[h], alpha=0.7)
               for h in HOV_ORDER]
    handles += [
        plt.Line2D([], [], color=INK, lw=1.5),
        plt.Line2D([], [], marker="o", color="white", markeredgecolor=INK_2,
                   lw=0, markersize=6),
    ]
    labels = [HOV_LABEL[h] for h in HOV_ORDER] + ["Mittelwert", "Median (Balken = IQR)"]
    ax.legend(handles, labels, frameon=False, fontsize=8.5, **kw)


# ---------------------------------------------------------------------------
# Plot 1: 10 Basiswerte
# ---------------------------------------------------------------------------
def plot_basic(df: pd.DataFrame, out_dir: Path, source_label: str = "ESS11, DE") -> None:
    fig, ax = plt.subplots(figsize=(11, 5.2))
    data = [df[c].to_numpy() for c, _, _ in BASIC]
    colors = [HOV_COLOR[h] for _, _, h in BASIC]
    _violins(ax, data, colors)
    _zero_line(ax, "persönl.\nMittel (MRAT)")
    ax.set_xticks(range(1, len(BASIC) + 1))
    ax.set_xticklabels([f"{lab}\n({c})" for c, lab, _ in BASIC], fontsize=8.5)
    ax.set_ylabel("Wichtigkeit relativ zum persönlichen Mittel\n(MRAT-zentriert)")
    ax.set_title(f"Die 10 Schwartz-Basiswerte – Verteilung über {len(df)} Personen ({source_label})", pad=22)
    ax.text(0, 1.01, "Reihenfolge entlang des Wertekreises; Farbe = Higher-Order Value",
            transform=ax.transAxes, fontsize=9, color=INK_2, va="bottom")
    _legend_hov(ax, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.32))
    _save(fig, out_dir, "plot1_basiswerte")


# ---------------------------------------------------------------------------
# Plot 2: 4 Higher-Order Values
# ---------------------------------------------------------------------------
def _pair_panel(ax: plt.Axes, df: pd.DataFrame, xcol: str, ycol: str,
                lim: tuple[float, float]) -> None:
    hb = ax.hexbin(df[xcol], df[ycol], gridsize=28, cmap=SEQ_BLUE, mincnt=1,
                   extent=(*lim, *lim), linewidths=0.2, edgecolors="white")
    ax.plot(lim, lim[::-1], color=INK_2, lw=1, ls=":", zorder=3)  # x + y = 0
    ax.axhline(0, color=GRID, lw=0.8, zorder=0)
    ax.axvline(0, color=GRID, lw=0.8, zorder=0)
    r = df[xcol].corr(df[ycol])
    ax.text(0.97, 0.97, f"r = {r:.2f}", transform=ax.transAxes, ha="right",
            va="top", fontsize=10, color=INK)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_aspect("equal")
    ax.set_xlabel(f"{HOV_LABEL[xcol]} ({xcol})", color=HOV_COLOR[xcol])
    ax.set_ylabel(f"{HOV_LABEL[ycol]} ({ycol})", color=HOV_COLOR[ycol])
    return hb


def plot_higher_order(df: pd.DataFrame, out_dir: Path) -> None:
    fig = plt.figure(figsize=(14, 5.2))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1], wspace=0.35)

    ax = fig.add_subplot(gs[0])
    data = [df[h].to_numpy() for h in HOV_ORDER]
    _violins(ax, data, [HOV_COLOR[h] for h in HOV_ORDER])
    _zero_line(ax)
    ax.set_xticks(range(1, 5))
    short = {"OPEN": "Offenheit", "SELFENH": "Selbst-\nstärkung",
             "CONS": "Bewahrung", "SELFTRANS": "Selbst-\ntranszendenz"}
    ax.set_xticklabels([f"{short[h]}\n({h})" for h in HOV_ORDER], fontsize=8.5)
    ax.set_ylabel("MRAT-zentriert")
    ax.set_title("A  Verteilung der 4 Higher-Order Values")

    lim = (-3.5, 3.0)
    ax_b = fig.add_subplot(gs[1])
    _pair_panel(ax_b, df, "OPEN", "CONS", lim)
    ax_b.set_title("B  Offenheit vs.\n    Bewahrung")
    ax_c = fig.add_subplot(gs[2])
    hb = _pair_panel(ax_c, df, "SELFENH", "SELFTRANS", lim)
    ax_c.set_title("C  Selbststärkung vs.\n    Selbsttranszendenz")
    cb = fig.colorbar(hb, ax=[ax_b, ax_c], shrink=0.7, pad=0.06)
    cb.set_label("Anzahl Personen je Feld", color=INK_2)
    cb.outline.set_visible(False)

    fig.text(0.5, -0.02,
             "B/C: gepunktete Diagonale = perfekter Gegensatz (beide Pole gleich weit vom "
             "persönl. Mittel). Negative Korrelation bestätigt die bipolare Struktur, "
             "auf der die x/y-Achsen beruhen.",
             ha="center", fontsize=8.5, color=INK_2)
    _save(fig, out_dir, "plot2_higher_order")


# ---------------------------------------------------------------------------
# Plot 3: 2D-Ebene x/y
# ---------------------------------------------------------------------------
def plot_xy(df: pd.DataFrame, out_dir: Path, source_label: str = "ESS11, DE") -> None:
    x, y = df["x"].to_numpy(), df["y"].to_numpy()
    lim_x, lim_y = (-4.5, 5.5), (-4.5, 4.5)

    fig = plt.figure(figsize=(9, 8.3))
    gs = fig.add_gridspec(2, 2, width_ratios=[4, 0.9], height_ratios=[0.9, 4],
                          wspace=0.04, hspace=0.04)
    ax = fig.add_subplot(gs[1, 0])
    ax_top = fig.add_subplot(gs[0, 0], sharex=ax)
    ax_right = fig.add_subplot(gs[1, 1], sharey=ax)

    hb = ax.hexbin(x, y, gridsize=(34, 26), cmap=SEQ_BLUE, mincnt=1,
                   extent=(*lim_x, *lim_y), linewidths=0.2, edgecolors="white")
    ax.axhline(0, color=INK_2, lw=1)
    ax.axvline(0, color=INK_2, lw=1)
    ax.scatter(x.mean(), y.mean(), s=110, marker="X", color="#e34948",
               edgecolor="white", lw=1.5, zorder=5)
    ax.annotate(f"Mittelwert\n({x.mean():.2f} | {y.mean():.2f})",
                (x.mean(), y.mean()), xytext=(14, -26), textcoords="offset points",
                fontsize=8.5, color=INK)
    ax.set_xlim(lim_x)
    ax.set_ylim(lim_y)
    ax.set_xlabel("x = SELFTRANS − SELFENH\n"
                  "← eigener Erfolg / Status          Gemeinwohl / andere →")
    ax.set_ylabel("y = OPEN − CONS\n"
                  "← Sicherheit / Tradition          Wandel / Unabhängigkeit →")

    # Quadranten-Anteile
    n = len(df)
    quads = [
        ((x > 0) & (y > 0), (0.98, 0.98), "right", "top", "offen &\nselbsttranszendent"),
        ((x < 0) & (y > 0), (0.02, 0.98), "left", "top", "offen &\nselbststärkend"),
        ((x < 0) & (y < 0), (0.02, 0.02), "left", "bottom", "bewahrend &\nselbststärkend"),
        ((x > 0) & (y < 0), (0.98, 0.02), "right", "bottom", "bewahrend &\nselbsttranszendent"),
    ]
    for mask, pos, ha, va, lab in quads:
        ax.text(*pos, f"{lab}\n{mask.sum() / n:.0%}", transform=ax.transAxes,
                ha=ha, va=va, fontsize=9, color=INK_2,
                multialignment=ha if ha != "right" else "right")
    on_axis = (np.isclose(x, 0) | np.isclose(y, 0)).mean()
    ax.text(0.5, 0.01, f"{on_axis:.1%} liegen genau auf einer Achse (x = 0 oder y = 0)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=INK_2)

    bins_x = np.arange(lim_x[0], lim_x[1] + 0.25, 0.25)
    # y liegt auf einem 1/6-Raster -> Klassenbreite 1/3, um das Raster zentriert
    bins_y = np.arange(lim_y[0] - 1 / 6, lim_y[1] + 1 / 3, 1 / 3)
    ax_top.hist(x, bins=bins_x, color="#3987e5", edgecolor="white", lw=0.5)
    ax_right.hist(y, bins=bins_y, color="#3987e5", edgecolor="white", lw=0.5,
                  orientation="horizontal")
    ax_top.axvline(0, color=INK_2, lw=1)
    ax_right.axhline(0, color=INK_2, lw=1)
    for a in (ax_top, ax_right):
        a.tick_params(labelbottom=False, labelleft=False, length=0)
        for s in a.spines.values():
            s.set_visible(False)

    cax = fig.add_subplot(gs[0, 1])
    cax.axis("off")
    cb = fig.colorbar(hb, ax=cax, location="left", fraction=0.6, shrink=0.9, pad=0)
    cb.set_label("Personen\nje Feld", color=INK_2, fontsize=8.5)
    cb.outline.set_visible(False)

    ax_top.set_title(f"Personen im 2D-Wertekreis (n = {n}, {source_label})", pad=10)
    _save(fig, out_dir, "plot3_wertekreis_xy")


def make_figures(scores_csv: str | Path, out_dir: str | Path, source_label: str = "ESS11, DE") -> list[Path]:
    """Erzeugt alle drei Abbildungen aus der Scores-CSV und gibt die PNG-Pfade zurück."""
    out_dir = Path(out_dir)
    df = pd.read_csv(scores_csv, dtype={"id": str})
    plot_basic(df, out_dir, source_label)
    plot_higher_order(df, out_dir)
    plot_xy(df, out_dir, source_label)
    return [out_dir / f"{n}.png" for n in ("plot1_basiswerte", "plot2_higher_order", "plot3_wertekreis_xy")]
