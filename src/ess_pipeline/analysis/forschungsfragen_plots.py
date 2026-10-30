"""
Abbildungen zu den Forschungsfragen im Stil des Dashboards (Schwartz_KI_vs_Real_Dashboard.html):
ein Panel pro Abbildung, eine Aussage, kurzer Titel als Frage, darunter die Antwort mit Zahl.
Person = Blau, Twin = Orange, Vergleichsgrößen = warmes Grau. Jede Abbildung hat eine Fußzeile mit N,
Datengrundlage (gezogene Antworten oder Erwartungswerte) und Testverfahren.

Feste Begriffe: Person, Twin, Mittelwert, Demografie-Mittelwert,
individuelle Abweichung, Milieu 1/2 mit Namen, deutsche Wertenamen, „Form“ nur für die Verteilungsform (2c).
Titel, Dateiname und Übersicht im Report tragen dieselbe Nummer.
Twin-Marker überall gleich: gefüllter oranger Punkt = gezogene Antwort, oranger Ring = Erwartungswert.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, PercentFormatter

from ..plotting import BASIC
from .data import BASIC_VALUES, ITEM_VALUE

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, REF = "#e1e0d9", "#c3c2b7", "#a8a7a0"
REAL, KI, ACCENT = "#2a78d6", "#eb6834", "#6250d6"
NEG, POS = "#199e70", "#d55181"
UNDER, OVER = "#6f66a8", "#b0894a"   # 1c: nur Richtung, ohne Wertung
MILIEU = ["#1baf7a", "#6250d6"]
VALUE_NAME = {code: name.replace("-\n", "").replace("\n", " ") for code, name, _ in BASIC}
ITEM_SHORT = {
    "ipcrtiva": "kreativ sein", "impricha": "reich sein", "ipeqopta": "Gleichbehandlung",
    "ipshabta": "Fähigkeiten zeigen", "impsafea": "sichere Umgebung", "impdiffa": "Abwechslung",
    "ipfrulea": "Regeln befolgen", "ipudrsta": "andere verstehen", "ipmodsta": "bescheiden sein",
    "ipgdtima": "Spaß haben", "impfreea": "frei entscheiden", "iphlppla": "anderen helfen",
    "ipsucesa": "erfolgreich sein", "ipstrgva": "starker Staat", "ipadvnta": "Abenteuer",
    "ipbhprpa": "korrekt verhalten", "iprspota": "Respekt erhalten", "iplylfra": "Freunden loyal",
    "impenva": "Umwelt schützen", "imptrada": "Tradition", "impfuna": "Vergnügen",
}

STYLE = {
    "font.family": ["Arial", "Arial Unicode MS"],
    "font.sans-serif": ["Arial", "Arial Unicode MS", "DejaVu Sans"],
    "font.size": 9.5,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False, "axes.spines.bottom": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "xtick.major.size": 0, "ytick.major.size": 0, "xtick.major.pad": 4, "ytick.major.pad": 6,
    "figure.facecolor": "white", "savefig.facecolor": "white", "axes.facecolor": "white",
    "legend.frameon": False, "legend.fontsize": 8.5,
}


# ---------------------------------------------------------------------------
# Bausteine
# ---------------------------------------------------------------------------

def de(x: float, nd: int = 2) -> str:
    return f"{x:.{nd}f}".replace(".", ",").replace("-", "−")


def signed(x: float, nd: int = 2) -> str:
    x = round(x, nd) + 0.0   # kein „−0,00“
    return ("+" if x > 0 else "") + de(x, nd)


def num(n: int) -> str:
    """Ganzzahl mit Leerzeichen als Tausendertrennzeichen (2 262)."""
    return f"{n:,}".replace(",", " ")


def pct(x: float) -> str:
    return f"{x * 100:.0f} %"


def light(color: str, a: float = 0.4) -> str:
    """Farbe auf Weiß mit Deckkraft a (blass = nicht signifikant / schlechter)."""
    return to_hex(tuple(a * c + (1 - a) for c in to_rgb(color)))


def over_white(*layers: tuple[str, float]) -> str:
    """Mischfarbe übereinandergelegter halbtransparenter Flächen auf Weiß."""
    rgb = np.ones(3)
    for c, a in layers:
        rgb = a * np.array(to_rgb(c)) + (1 - a) * rgb
    return to_hex(tuple(rgb))


def comma_axis(ax: plt.Axes, axis: str = "x") -> None:
    getattr(ax, f"{axis}axis").set_major_formatter(
        FuncFormatter(lambda v, _: f"{round(v, 6):g}".replace(".", ",").replace("-", "−")))


def figure(w: float, h: float, **kw):
    plt.rcParams.update(STYLE)
    return plt.subplots(figsize=(w, h), **kw)


def subplots(*args, **kw):
    plt.rcParams.update(STYLE)
    return plt.subplots(*args, **kw)


def _handle(color: str, label: str, kind: str) -> Line2D:
    """Legenden-Symbol: dot, ring (hohler Kreis), sq (Fläche), hatch (schraffierte blasse Fläche), dash, line."""
    if kind == "hatch":
        return Patch(facecolor=light(color), edgecolor=color, hatch="////", lw=0, label=label)
    if kind in ("dash", "line"):
        return Line2D([], [], ls="--" if kind == "dash" else "-", lw=1.8, color=color, label=label)
    marker = {"dot": "o", "ring": "o", "sq": "s"}[kind]
    hollow = kind == "ring"
    return Line2D([], [], marker=marker, ls="", color=color, mfc="white" if hollow else color, mec=color,
                  mew=1.6 if hollow else 0, ms=7 if hollow else 8, label=label)


def header(fig: plt.Figure, title: str, sub: str, keys: list[tuple[str, str, str]] | None = None,
           extra: float = 0.0, footer: str | None = None, ncol: int | None = None) -> None:
    """
    Kopf wie im Dashboard: Titel (Frage), darunter die Antwort, darunter optional der Farbschlüssel.
    Alles linksbündig; die genaue x-Position setzt save() auf den linken Rand der Achsenbeschriftung.
    `extra` = zusätzlicher Abstand (Zoll) für Achsentitel unter dem Kopf. `footer` = Fußzeile (N, Daten, Test).
    """
    h = fig.get_figheight()
    lines = sub.count("\n") + 1
    y_sub = 0.40
    y_keys = y_sub + 0.19 * lines + 0.10
    ncol = ncol or (len(keys) if keys else 1)
    rows = -(-len(keys) // ncol) if keys else 0
    top = y_keys + (0.06 + 0.24 * rows if keys else 0.0) + extra
    fig.subplots_adjust(top=1 - top / h)
    texts = [fig.text(0, 1 - 0.10 / h, title, ha="left", va="top", fontsize=12.5, fontweight="bold", color=INK),
             fig.text(0, 1 - y_sub / h, sub, ha="left", va="top", fontsize=9.5, color=INK2, linespacing=1.45)]
    fig._ff_header = texts
    fig._ff_footer = footer
    if keys:
        handles = [_handle(c, lab, kind) for c, lab, kind in keys]
        fig._ff_legend = fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, 1 - y_keys / h),
                                    ncol=ncol, frameon=False, handletextpad=0.45, columnspacing=1.6,
                                    labelcolor=INK2, fontsize=9, borderaxespad=0, borderpad=0, labelspacing=0.5,
                                    handlelength=1.6 if any(k in ("dash", "line") for *_, k in keys) else 0.8)


def save(fig: plt.Figure, out: Path, name: str) -> None:
    """Kopf und Fußzeile bündig mit dem linken Rand der Achsenbeschriftungen ausrichten, dann speichern."""
    renderer = fig.canvas.get_renderer()
    boxes = [ax.get_tightbbox(renderer) for ax in fig.axes]
    w_px, h_px = fig.dpi * fig.get_figwidth(), fig.dpi * fig.get_figheight()
    x0 = min(b.x0 for b in boxes) / w_px
    for t in getattr(fig, "_ff_header", []):
        t.set_x(x0)
    leg = getattr(fig, "_ff_legend", None)
    if leg is not None:
        anchor = leg.get_bbox_to_anchor().transformed(fig.transFigure.inverted())
        leg.set_bbox_to_anchor((x0, anchor.y0), transform=fig.transFigure)
    footer = getattr(fig, "_ff_footer", None)
    if footer:
        y0 = min(b.y0 for b in boxes) / h_px
        fig.text(x0, y0 - 0.14 / fig.get_figheight(), footer, ha="left", va="top", fontsize=8, color=MUTED,
                 linespacing=1.45)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.png", dpi=220, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


def vgrid(ax: plt.Axes) -> None:
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def hgrid(ax: plt.Axes) -> None:
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def ylabels(ax: plt.Axes, y, labels, strong=None) -> None:
    ax.set_yticks(y, labels)
    for lab, s in zip(ax.get_yticklabels(), strong or [False] * len(labels), strict=False):
        lab.set_color(INK if s else INK2)
        lab.set_fontsize(9)
        if s:
            lab.set_fontweight("semibold")


def dumbbell(ax: plt.Axes, y, a, b, ca=REAL, cb=KI) -> None:
    ax.hlines(y, a, b, color=AXIS, lw=2, zorder=1)
    ax.scatter(a, y, s=58, color=ca, edgecolor="white", lw=1.5, zorder=3)
    ax.scatter(b, y, s=58, color=cb, edgecolor="white", lw=1.5, zorder=3)


def item_label(item: str, qno: dict[str, int]) -> str:
    """„Spaß haben  ·  Hedonismus, Q10“: Inhalt der Frage, deutscher Wertename, Fragenummer."""
    return f"{ITEM_SHORT[item]}  ·  {VALUE_NAME[ITEM_VALUE[item]]}, Q{qno[item]}"


def footer_text(n: int, data: str, test: str | None = None) -> str:
    return " · ".join([f"N = {num(n)} Personen", data] + ([test] if test else []))


# ---------------------------------------------------------------------------
# A1 Beispielperson
# ---------------------------------------------------------------------------

def _example_items(h: np.ndarray, drawn: np.ndarray, e: np.ndarray) -> list[int]:
    """Drei Fragen, die das Prinzip zeigen: Treffer, Ziehung weit vom Erwartungswert, Modell schon im Mittel daneben."""
    order = []
    hit = np.flatnonzero(drawn == h)
    order.append(int(hit[np.argmin(np.abs(e[hit] - h[hit]))]) if len(hit) else int(np.argmin(np.abs(drawn - h))))
    for score in (np.abs(drawn - e), np.abs(e - h)):
        for j in np.argsort(-score):
            if j not in order:
                order.append(int(j))
                break
    return order


def fig_a1(pid: str, h: np.ndarray, drawn: np.ndarray, e: np.ndarray, p: np.ndarray, qno: dict[str, int],
           run_name: str, out: Path) -> None:
    """Eine Person und ihr Twin. Arrays in PVQ_ITEMS-Reihenfolge, umgepolt (6 = sehr wichtig); p: (21, 6)."""
    from ..config import PVQ_ITEMS
    q_order = sorted(range(len(PVQ_ITEMS)), key=lambda j: qno[PVQ_ITEMS[j]])
    ex = _example_items(h, drawn, e)
    letters = {j: "ABC"[i] for i, j in enumerate(ex)}
    fig = plt.figure(figsize=(10.5, 7.8))
    plt.rcParams.update(STYLE)
    gs = fig.add_gridspec(3, 2, width_ratios=[1.55, 1], wspace=0.28, hspace=0.75)
    ax = fig.add_subplot(gs[:, 0])
    y = np.arange(len(q_order))[::-1]
    for yi, j in zip(y, q_order, strict=True):
        if j in letters:
            ax.axhspan(yi - 0.45, yi + 0.45, color="#f4f3ee", zorder=0)
            ax.text(6.55, yi, letters[j], va="center", ha="left", fontsize=9.5, fontweight="bold", color=INK)
        ax.plot([h[j], drawn[j]], [yi + 0.14, yi - 0.14], color=AXIS, lw=1.6, zorder=1)
    ax.scatter(h[q_order], y + 0.14, s=52, color=REAL, edgecolor="white", lw=1.2, zorder=3)
    ax.scatter(drawn[q_order], y - 0.14, s=52, color=KI, edgecolor="white", lw=1.2, zorder=3)
    ax.scatter(e[q_order], y - 0.14, s=40, facecolor="white", edgecolor=KI, lw=1.6, zorder=4)
    ylabels(ax, y, [item_label(PVQ_ITEMS[j], qno) for j in q_order])
    ax.set_xlim(0.6, 6.9)
    ax.set_ylim(-0.7, len(q_order) - 0.3)
    ax.set_xticks(range(1, 7))
    vgrid(ax)
    ax.set_xlabel("Antwort: 1 = „überhaupt nicht ähnlich“ … 6 = „sehr ähnlich“\n"
                  "(gegenüber dem Fragebogen umgepolt, damit hoch = wichtig)")

    for i, j in enumerate(ex):
        a = fig.add_subplot(gs[i, 1])
        k = np.arange(1, 7)
        a.bar(k, p[j], width=0.68, color=[KI if kk == drawn[j] else light(KI, 0.35) for kk in k])
        a.axvline(e[j], color=INK, lw=1.3, ls="--")
        a.scatter([h[j]], [0], marker="^", s=70, color=REAL, edgecolor="white", lw=1, clip_on=False, zorder=4)
        top = max(p[j].max(), 0.3) * 1.25
        a.text(e[j] + 0.08, top * 0.93, f"Erwartungswert {de(e[j], 1)}", fontsize=8, color=INK, va="top")
        a.set_ylim(0, top)
        a.set_xticks(k)
        a.set_xlim(0.4, 6.6)
        a.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        hgrid(a)
        a.set_title(f"{letters[j]}  {ITEM_SHORT[PVQ_ITEMS[j]]} · Q{qno[PVQ_ITEMS[j]]}", loc="left", fontsize=9.5,
                    color=INK, fontweight="semibold", pad=17)
        verdict = f"gezogen {int(drawn[j])}, Person {int(h[j])}" + (" · Treffer" if drawn[j] == h[j] else "")
        a.text(0, 1.03, verdict, transform=a.transAxes, ha="left", va="bottom", fontsize=8, color=INK2)
        if i == 1:
            a.set_ylabel("Wahrscheinlichkeit laut Modell")
    mae, mae_e = np.abs(drawn - h).mean(), np.abs(e - h).mean()
    header(fig, "A1  Wie entsteht ein Twin?",
           "So entsteht ein Twin: Das Modell gibt je Frage sechs Wahrscheinlichkeiten an, ein Programm zieht daraus "
           "die Antwort.\n"
           f"Bei dieser Person liegt der Twin im Mittel {de(mae)} Skalenpunkte daneben "
           f"(mit Erwartungswerten statt Ziehung: {de(mae_e)}).",
           keys=[(REAL, "Person (echte Antwort; ▲ in den Feldern rechts)", "dot"), (KI, "Twin, gezogene Antwort", "dot"),
                 (KI, "Twin, Erwartungswert Σ k · pk", "ring"), (light(KI, 0.35), "Wahrscheinlichkeit je Antwort",
                                                                 "sq")], extra=0.25,
           footer=f"Person {pid} (ESS 11, Deutschland) und ihr Twin · Lauf {run_name} · graue Linie = Fehler "
                  "der gezogenen Antwort\nRechts: drei Beispielfragen (A, B, C); kräftiger Balken = gezogene Antwort, "
                  "gestrichelt = Erwartungswert, ▲ = Antwort der Person")
    save(fig, out, "A1_beispielperson")


# ---------------------------------------------------------------------------
# Ebene 1
# ---------------------------------------------------------------------------

MAE_LABELS = {
    "Fremder Twin": "Fremder Twin\n(Twin einer anderen Person)",
    "Twin": "Twin",
    "Demografie-Mittelwert": "Demografie-Mittelwert\n(Geschlecht, Alter, Bildung)",
    "Mittelwert aller Personen": "Mittelwert aller Personen",
}
MAE_ACC = {"Fremder Twin": "den fremden Twin", "Demografie-Mittelwert": "den Demografie-Mittelwert",
           "Mittelwert aller Personen": "den Mittelwert"}
DATA_E1 = "Erwartungswerte Σ k · pk der Twins"   # Datengrundlage Ebene 1


def p_text(p: float) -> str:
    return "p < 0,001" if p < 0.001 else f"p = {de(p, 3)}"


def _join(xs: list[str]) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " und " + xs[-1]


def fig_1a(mae: dict[str, float], mae_g: float, p: float, n: int, out: Path) -> None:
    """mae: Twin und Vergleichsgrößen aus Erwartungswerten; mae_g: Twin mit gezogenen Antworten (gefüllter Punkt)."""
    names = sorted(mae, key=mae.get, reverse=True)
    vals = [mae[k] for k in names]
    y = np.arange(len(names))[::-1]
    fig, ax = figure(7.6, 4.0)
    cols = [KI if k == "Twin" else REF for k in names]
    ax.barh(y, vals, height=0.56, color=cols)
    for yi, v, k in zip(y, vals, names, strict=True):
        ax.text(v + 0.03, yi, de(v), va="center", fontsize=9, color=INK if k == "Twin" else INK2,
                fontweight="semibold" if k == "Twin" else None)
    yt = y[names.index("Twin")]
    ax.scatter([mae_g], [yt], s=58, color=KI, edgecolor="white", lw=1.5, zorder=4)
    ax.text(mae_g + 0.04, yt + 0.42, f"{de(mae_g)} mit gezogenen Antworten", ha="left", va="center", fontsize=8,
            color=INK)
    ylabels(ax, y, [MAE_LABELS[k] for k in names], [k == "Twin" for k in names])
    ax.set_xlim(0, max(max(vals), mae_g) + 0.45)
    vgrid(ax)
    comma_axis(ax)
    ax.set_xlabel("Mittlerer absoluter Fehler (MAE, Skalenpunkte auf der Skala 1–6)")
    worse = [MAE_ACC[k] for k in names if k != "Twin" and mae[k] > mae["Twin"]]
    better = [MAE_ACC[k] for k in names if k != "Twin" and mae[k] <= mae["Twin"]]
    verdict = (f"Er schlägt {_join(worse)}" if worse else "Er schlägt keine Vergleichsgröße")
    if better:
        verdict += f",\nverliert aber gegen {_join(better)}, die von der Person nichts wissen."
    header(fig, "1a  Wie weit liegt der Twin bei seiner Person daneben?",
           f"Kürzer = genauer. Der Twin liegt im Mittel {de(mae['Twin'])} Skalenpunkte daneben (mit gezogenen "
           f"Antworten {de(mae_g)}). {verdict}",
           keys=[(KI, "Twin (Erwartungswerte)", "sq"), (KI, "Twin, gezogene Antworten", "dot"),
                 (REF, "Vergleichsgrößen ohne Wissen über die Person", "sq")],
           footer=footer_text(n, f"je 21 Fragen · {DATA_E1} (Punkt: gezogene Antworten)",
                              f"Twin vs. fremder Twin: Wilcoxon-Test, {p_text(p)}"))
    save(fig, out, "FF1a_genauigkeit")


def fig_1b(rho: dict[str, tuple[float, float]], p: float, p_cell: float, n: int, out: Path) -> None:
    """rho[name] = (ganzes Profil, individuelle Abweichung). Rechts kein Balken für den fremden Twin (≈ 0 per
    Konstruktion). p: Twin vs. fremder Twin, p_cell: Twin vs. Demografie-Mittelwert (rechts, je Person gepaart)."""
    series = [("Twin", KI), ("Demografie-Mittelwert", INK2), ("Fremder Twin", REF)]
    groups = ["Ganzes Werteprofil\n(Rangfolge aller 21 Fragen)", "Nur individuelle Abweichung\n(Mittelwert je Frage "
                                                                 "abgezogen)"]
    fig, ax = figure(7.6, 4.6)
    bw = 0.22
    for j, (name, col) in enumerate(series):
        for g in range(2):
            v = rho[name][g]
            x = g + (j - 1) * (bw + 0.03)
            if g == 1 and name == "Fremder Twin":
                ax.text(x, 0.012, f"fremder\nTwin\n{de(v)}", ha="center", va="bottom", fontsize=8, color=MUTED)
                continue
            ax.bar(x, v, width=bw, color=col)
            ax.text(x, max(v, 0) + 0.012, de(v), ha="center", va="bottom", fontsize=8.5,
                    color=INK if name == "Twin" else INK2, fontweight="semibold" if name == "Twin" else None)
    ax.set_xticks(range(2), groups)
    ax.set_xlim(-0.42, 1.42)   # Platz für die Beschriftung des fremden Twins rechts innerhalb der Achse
    for lab in ax.get_xticklabels():
        lab.set_color(INK2)
        lab.set_fontsize(9.5)
    ax.axhline(0, color=AXIS, lw=1)
    ax.set_ylim(0, max(v for pair in rho.values() for v in pair) + 0.1)
    hgrid(ax)
    comma_axis(ax, "y")
    ax.set_ylabel("Spearman ρ, Mittel über alle Twins\n(1 = gleiche Rangfolge, 0 = kein Zusammenhang)")
    tw, dm = rho["Twin"][1], rho["Demografie-Mittelwert"][1]
    # Wilcoxon wird bei N = 2 262 schon bei winzigen Differenzen signifikant: unter 0,05 Abstand gilt als gleichauf
    if abs(tw - dm) < 0.05:
        verdict = (f"etwa so viel, wie Geschlecht, Alter und Bildung allein verraten ({de(tw)} gegen {de(dm)}"
                   + (", knapp gesichert" if p_cell < 0.05 else ", nicht gesichert") + ")")
    else:
        verdict = ("mehr, als Geschlecht, Alter und Bildung allein verraten" if tw > dm else
                   "aber weniger, als Geschlecht, Alter und Bildung allein verraten")
    header(fig, "1b  Trifft der Twin, was seiner Person wichtig ist?",
           "Links die Rangfolge aller 21 Fragen, rechts nur die individuelle Abweichung. Der Twin weiß etwas über "
           f"die Person,\nbei der individuellen Abweichung {verdict}.",
           keys=[(c, nm, "sq") for nm, c in series],
           footer=footer_text(n, DATA_E1, f"rechts, Wilcoxon-Test je Person gepaart: Twin vs. fremder Twin "
                                          f"{p_text(p)}, Twin vs. Demografie-Mittelwert {p_text(p_cell)}"))
    save(fig, out, "FF1b_profil")


def fig_a3(twins: pd.DataFrame, n: int, out: Path) -> None:
    """Vergleich je Person: Twin minus Vergleichsgröße derselben Person, für den MAE (links) und das ρ der
    individuellen Abweichung (rechts). Der Anteil auf der guten Seite der 0 ist direkt der Anteil der Twins, die
    besser sind. Fremder Twin: Mittel über 20 Zufallspaarungen je Person wie in 1a."""
    fig, axes = subplots(1, 2, figsize=(10.5, 4.6), gridspec_kw={"wspace": 0.22})
    panels = [
        (axes[0], "mae", "mae_zellmittel", "mae_zufallspaarung", np.linspace(-1.0, 1.0, 41),
         "MAE des Twins minus MAE der Vergleichsgröße (Skalenpunkte)", "Fehler  ·  links der 0 = Twin genauer", -1),
        (axes[1], "spearman_abweichung", "spearman_abweichung_zellmittel", "spearman_abweichung_zufallspaarung",
         np.linspace(-1.0, 1.0, 41), "ρ des Twins minus ρ der Vergleichsgröße",
         "Individuelle Abweichung  ·  rechts der 0 = Twin besser", 1),
    ]
    shares = []
    for ax, c_twin, c_cell, c_shuf, edges, xlabel, title, good in panels:
        for col, color, fill in [(c_shuf, REF, False), (c_cell, KI, True)]:
            d = (twins[c_twin] - twins[col]).dropna()
            v, _ = np.histogram(d, bins=edges)
            v = v / v.sum()
            ax.stairs(v, edges, color=color, lw=1.6)
            if fill:
                ax.stairs(v, edges, color=color, alpha=0.18, fill=True)
        top = ax.get_ylim()[1] * 1.25
        ax.axvline(0, color=INK, lw=1.2)
        better = (lambda a, b: a < b) if good < 0 else (lambda a, b: a > b)
        s_cell = float(better(twins[c_twin], twins[c_cell]).mean())
        s_shuf = float(better(twins[c_twin], twins[c_shuf]).mean())
        shares.append(s_cell)
        x_txt = edges[0] + 0.03 * (edges[-1] - edges[0]) if good < 0 else edges[-1] - 0.03 * (edges[-1] - edges[0])
        ax.text(x_txt, top * 0.97, f"Twin besser als …\nDemografie-Mittelwert: {pct(s_cell)}\nfremder Twin: "
                f"{pct(s_shuf)}", ha="left" if good < 0 else "right", va="top", fontsize=8.5, color=INK,
                linespacing=1.5)
        ax.set_ylim(0, top)
        ax.set_xlim(edges[0], edges[-1])
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        comma_axis(ax)
        hgrid(ax)
        ax.set_xlabel(xlabel)
        ax.set_title(title, loc="left", fontsize=10, color=INK, fontweight="semibold", pad=10)
    axes[0].set_ylabel("Anteil der Personen")
    header(fig, "A3  Gibt es einzelne gute Twins?",
           f"Beim Abstand wenige: Nur bei {pct(shares[0])} der Personen liegt der Twin näher als ihr "
           f"Demografie-Mittelwert (Fläche links der 0).\nBei der individuellen Abweichung ist es {pct(shares[1])}, "
           "also etwa jeder zweite."
           if shares[0] < 0.5 else
           f"Bei {pct(shares[0])} der Personen liegt der Twin näher als ihr Demografie-Mittelwert, bei der "
           f"individuellen Abweichung bei {pct(shares[1])}.",
           keys=[(KI, "Twin gegen Demografie-Mittelwert derselben Person", "sq"),
                 (REF, "Twin gegen fremden Twin", "sq"), (INK, "0 = gleich gut", "line")],
           footer=footer_text(n, f"{DATA_E1} · je Person ein Wert über 21 Fragen",
                              "ρ: Spearman nach Abzug des Mittelwerts je Frage\nFremder Twin: Mittel über 20 "
                              "Zufallspaarungen je Person wie in 1a"),
           extra=0.2)
    save(fig, out, "A3_fehler_je_twin")


def fig_1b2(items: pd.DataFrame, qno: dict[str, int], n: int, out: Path) -> None:
    """Kräftig = Twin gesichert besser als der Demografie-Mittelwert (95-%-Bootstrap-Intervall der Differenz über 0).
    Die Zahlen stehen in zwei festen Spalten rechts, damit klar ist, welche Zahl zu Balken und Punkt gehört."""
    df = items.sort_values("spearman_item").reset_index(drop=True)
    y = np.arange(len(df))
    sure = df["besser_als_zellmittel_gesichert"].to_numpy()
    worse = df["schlechter_als_zellmittel_gesichert"].to_numpy()
    fig, ax = figure(7.6, 7.2)
    ax.barh(y, df["spearman_item"], height=0.62, color=[KI if b else light(KI) for b in sure],
            hatch=["////" if w else None for w in worse], edgecolor=[KI if w else "none" for w in worse], lw=0)
    ax.hlines(y, df["spearman_item_ci_unten"], df["spearman_item_ci_oben"], color=INK, lw=1, zorder=2)
    ax.scatter(df["spearman_item_zellmittel"], y, s=30, color=INK2, edgecolor="white", lw=1, zorder=3)
    hi = max(df["spearman_item_ci_oben"].max(), df["spearman_item_zellmittel"].max())
    c_tw, c_dm = hi + 0.06, hi + 0.15   # Spalten für die Zahlen
    for yi, v, z in zip(y, df["spearman_item"], df["spearman_item_zellmittel"], strict=True):
        ax.text(c_tw, yi, de(v), va="center", ha="right", fontsize=8.5, color=INK, fontweight="semibold")
        ax.text(c_dm, yi, de(z), va="center", ha="right", fontsize=8.5, color=INK2)
    ax.text(c_tw, len(df) - 0.2, "Twin", ha="right", va="bottom", fontsize=8.5, color=INK, fontweight="semibold")
    ax.text(c_dm, len(df) - 0.2, "Demo.", ha="right", va="bottom", fontsize=8.5, color=INK2)
    ylabels(ax, y, [item_label(i, qno) for i in df["item"]])
    ax.axvline(0, color=AXIS, lw=1)
    ax.set_xlim(min(-0.03, df[["spearman_item_ci_unten", "spearman_item_zellmittel"]].min().min() - 0.02), c_dm + 0.01)
    ax.set_ylim(-0.7, len(df) + 0.3)
    ax.set_xticks([t for t in np.arange(0, hi + 0.001, 0.1)])
    vgrid(ax)
    comma_axis(ax)
    ax.set_xlabel("Spearman ρ zwischen Person und Twin bei dieser Frage, über alle Personen", loc="left")
    lead_dm = df["spearman_item"] - df["spearman_item_zellmittel"]   # Vorsprung gegenüber der Demografie
    top3 = [ITEM_SHORT[i] for i in df.loc[lead_dm.sort_values(ascending=False).index[:3], "item"]]
    better = (df["spearman_item"] > df["spearman_item_zellmittel"]).to_numpy()
    lead = ("Schwach, aber meist besser als der Demografie-Mittelwert" if better.sum() > len(df) / 2 else
            "Nur schwach und meist schlechter als der Demografie-Mittelwert")
    header(fig, "1b′  Unterscheidet der Twin die Personen bei einer Frage?",
           f"{lead}: gesichert besser bei {sure.sum()} von {len(df)} Fragen (kräftig), gesichert schlechter bei "
           f"{worse.sum()} (schraffiert).\nDer größte Vorsprung bei „{top3[0]}“, „{top3[1]}“ und „{top3[2]}“; ein ρ "
           "von 0,3 ist ein schwacher Zusammenhang.",
           keys=[(KI, "Twin gesichert besser als Demografie-Mittelwert", "sq"),
                 (light(KI), "nicht gesichert verschieden", "sq"), (KI, "gesichert schlechter", "hatch"),
                 (INK2, "Demografie-Mittelwert", "dot"), (INK, "95-%-Intervall (Twin)", "line")], ncol=2,
           footer=footer_text(n, DATA_E1,
                              "Demografie-Mittelwert: Mittel der anderen Personen gleichen Geschlechts, Alters "
                              "und Bildungsgrads\n„gesichert“: 95-%-Intervall der Differenz Twin − Demografie-"
                              f"Mittelwert über 0, gepaarter Bootstrap über Personen ({num(1000)} Stichproben)"))
    save(fig, out, "FF1b2_trennschaerfe")


def fig_1c(items: pd.DataFrame, qno: dict[str, int], n: int, out: Path) -> None:
    df = items.sort_values("me", ascending=False).reset_index(drop=True)
    y = np.arange(len(df))
    fig, ax = figure(7.6, 7.0)
    for yi, r in zip(y, df.itertuples(), strict=True):
        col = UNDER if r.me < 0 else OVER
        ax.barh(yi, r.me, height=0.62, color=col if r.signifikant else light(col, 0.3))
        ax.hlines(yi, r.me_ci_unten, r.me_ci_oben, color=INK if r.signifikant else MUTED, lw=1.1, zorder=3)
        end = r.me_ci_oben if r.me >= 0 else r.me_ci_unten
        ax.text(end + (0.03 if r.me >= 0 else -0.03), yi, signed(r.me), va="center",
                ha="left" if r.me >= 0 else "right", fontsize=8.5, color=INK2)
    # Mittlerer Fehler über alle Fragen = Antwortstil. Zentriert man je Person, verschiebt sich jeder Balken um genau
    # diesen Wert (per Konstruktion); der Abstand eines Balkens zur Linie ist also die Umgewichtung dieses Werts.
    style = df["me"].mean()
    ax.axvline(style, color=INK, lw=1.1, ls="--", zorder=1)
    ylabels(ax, y, [item_label(i, qno) for i in df["item"]])
    ax.axvline(0, color=AXIS, lw=1.2)
    lo, hi = df["me_ci_unten"].min() - 0.3, df["me_ci_oben"].max() + 0.3
    ax.set_xlim(lo, hi)
    ax.set_ylim(-0.7, len(df) - 0.3)
    vgrid(ax)
    comma_axis(ax)
    ax.text(lo + 0.02, len(df) - 0.25, "◀ Twin hält für unwichtiger", fontsize=8.5, color=MUTED, va="bottom")
    ax.text(hi - 0.02, len(df) - 0.25, "Twin hält für wichtiger ▶", fontsize=8.5, color=MUTED, va="bottom",
            ha="right")
    ax.set_xlabel("Mittlere Abweichung Twin − Person (Skalenpunkte auf der Skala 1–6)")
    n_sig = int(df["signifikant"].sum())
    header(fig, "1c  Liegt der Twin systematisch daneben?",
           f"Ja, bei {n_sig} von 21 Fragen (blass = nicht signifikant). Spaß, Erfolg und Kreativität sind dem "
           "Twin weniger\nwichtig als der Person, Regeln und korrektes Verhalten wichtiger.",
           keys=[(UNDER, "unwichtiger (Farbe zeigt nur die Richtung)", "sq"), (OVER, "wichtiger", "sq"),
                 (light(INK2, 0.3), "blass = nicht signifikant", "sq"), (INK, "95-%-Konfidenzintervall", "line"),
                 (INK, f"mittlerer Fehler aller Fragen ({signed(style)}, Antwortstil)", "dash")],
           ncol=2,
           footer=footer_text(n, DATA_E1, "t-Test je Frage, Holm-korrigiert über 21 Fragen (α = 0,05)\n"
                                          f"Gestrichelt: Über alle Fragen antwortet der Twin {de(abs(style))} Punkte "
                                          "niedriger (Antwortstil). Zentriert man je Person wie in Ebene 2, verschiebt "
                                          "sich jeder\nBalken um genau diesen Wert; der Abstand zur Linie ist die "
                                          "Umgewichtung des Werts (gegen die Linie signifikant: "
                                          f"{int(df['signifikant_zentriert'].sum())} von 21, Holm)."))
    save(fig, out, "FF1c_bias")


def fig_1d(groups: pd.DataFrame, tests: pd.DataFrame, overall: float, n: int, out: Path) -> None:
    sig = tests.set_index("merkmal")["p_holm"] < 0.05
    rows = []   # (label, wert | None, signifikant, ist_kopf)
    for var in tests["merkmal"]:
        rows.append((f"{var}*" if var == "Werte-Milieu" else var, None, sig[var], True))
        for r in groups[groups.merkmal == var].itertuples():
            rows.append((f"{r.gruppe}  (n = {num(r.n)})", r.mae, sig[var], False))
    y = np.arange(len(rows))[::-1]
    fig, ax = figure(7.6, 8.4)
    diffs = []
    for yi, (_, v, s, head) in zip(y, rows, strict=True):
        if head:
            continue
        d = v - overall
        diffs.append(abs(d))
        ax.barh(yi, d, height=0.62, color=(POS if d > 0 else NEG) if s else light(POS if d > 0 else NEG, 0.28))
        ax.text(d + (0.002 if d >= 0 else -0.002), yi, de(v), va="center", ha="left" if d >= 0 else "right",
                fontsize=8.5, color=INK2 if s else MUTED)
    labels = [lab if head else "   " + lab for lab, _, _, head in rows]
    ylabels(ax, y, labels, [head for *_, head in rows])
    ax.axvline(0, color=AXIS, lw=1.2)
    ax.set_xlim(-0.1, 0.1)
    ax.set_xticks(np.arange(-0.1, 0.101, 0.02))
    vgrid(ax)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: signed(v)))
    top = len(rows) - 0.3
    ax.set_ylim(-0.7, top + 0.6)
    ax.text(-0.099, top + 0.1, "◀ genauer als im Schnitt", fontsize=8.5, color=MUTED, va="bottom")
    ax.text(0.099, top + 0.1, "ungenauer ▶", fontsize=8.5, color=MUTED, va="bottom", ha="right")
    dmax = max(diffs)
    ax.set_xlabel(f"Fehler der Gruppe minus Gesamtfehler (MAE {de(overall)}); Zahl = MAE der Gruppe\n"
                  f"Achtung: Die Achse reicht nur bis ±0,1 Skalenpunkte. Der größte Unterschied ({de(dmax)}) "
                  f"entspricht {dmax / overall * 100:.0f} % des Fehlers.")
    def _worst(var):
        g = groups[groups.merkmal == var].sort_values("mae").gruppe.iloc[-1]
        return g if var == "Werte-Milieu" else f"{var} {g}"
    worst = [_worst(var) for var in tests["merkmal"] if sig[var]]
    lead = f"Ja, aber nur leicht (höchstens {de(dmax)} Skalenpunkte). Blass = nicht signifikant." if worst else "Nein."
    detail = f"\nAm ungenauesten: {_join(worst)}." if worst else ""
    header(fig, "1d  Trifft der Twin manche Gruppen schlechter?",
           f"{lead}{detail}",
           keys=[(POS, "ungenauer als im Schnitt", "sq"), (NEG, "genauer als im Schnitt", "sq"),
                 (light(INK2, 0.28), "blass = nicht signifikant", "sq")],
           footer=footer_text(n, f"je Merkmal ohne fehlende Angaben · {DATA_E1}",
                              f"einfaktorielle ANOVA je Merkmal, Holm-korrigiert über {len(tests)} Merkmale\n"
                              "* Werte-Milieu ist kein äußeres Merkmal, sondern aus den Antworten der Person selbst "
                              "gebildet (2.1). Der Effekt ist deshalb kein\nunabhängiger Gruppeneffekt, sondern "
                              "folgt aus dem Bias in 1c: Das Modell unterschätzt genau die Werte, die Milieu 1 prägen."))
    save(fig, out, "FF1d_subgruppen")


def fig_1e(vk: pd.DataFrame, qno: dict[str, int], out: Path) -> None:
    df = vk.assign(diff=vk.sd_llm - vk.sd_mensch).sort_values("diff").reset_index(drop=True)
    y = np.arange(len(df))
    fig, ax = figure(7.6, 7.4)
    for yi, r in zip(y, df.itertuples(), strict=True):
        ax.barh(yi, r.boot_oben - r.boot_unten, left=r.boot_unten, height=0.5, color=light(REAL, 0.22), zorder=0)
    dumbbell(ax, y, df["sd_mensch"], df["sd_llm"])
    ax.scatter(df["sd_llm_erwartung"], y, s=44, facecolor="white", edgecolor=KI, lw=1.6, zorder=3)
    ylabels(ax, y, [item_label(i, qno) for i in df["item"]])
    vgrid(ax)
    comma_axis(ax)
    ax.set_xlim(df["sd_llm_erwartung"].min() - 0.08, df[["sd_llm", "boot_oben"]].max().max() + 0.06)
    ax.set_xlabel("Standardabweichung der Antworten innerhalb gleicher Demografie (Skalenpunkte)")
    more = int((df["sd_llm"] > df["boot_oben"]).sum())
    narrow = int((df["sd_llm_erwartung"] < df["boot_unten"]).sum())
    header(fig, "1e  Werden die Twins einer Demografie-Gruppe zu ähnlich?",
           f"Ja, in ihren Erwartungswerten: Sie streuen bei {narrow} von 21 Fragen weniger als die Personen (Ringe).\n"
           f"Die gezogenen Antworten streuen dagegen bei {more} von 21 Fragen stärker; diese Breite stammt aus der "
           "Ziehung.",
           keys=[(REAL, "Personen", "dot"), (KI, "Twins, gezogene Antworten", "dot"),
                 (KI, "Twins, Erwartungswerte", "ring"), (light(REAL, 0.22), "95-%-Band der Personen", "sq")],
           footer=f"N = {num(vk.attrs['n_personen'])} Personen in {vk.attrs['n_zellen']} Demografie-Zellen "
                  "(Geschlecht × Alter × Bildung, je ≥ 20 Personen) · SD je Zelle, gewichtet gemittelt\n"
                  "Twins: gezogene Antworten und Erwartungswerte · Band: 1 000 Bootstrap-Stichproben der Personen "
                  "je Zelle · graue Linie = Abstand Person–Twin\nFragen sortiert nach dem Abstand gezogene Twins − "
                  "Personen (oben streuen die Twins am stärksten mehr)")
    save(fig, out, "FF1e_varianzkollaps")


def fig_a2(vz: pd.DataFrame, qno: dict[str, int], n: int, out: Path) -> None:
    df = vz.sort_values("var_twin_gesamt").reset_index(drop=True)
    y = np.arange(len(df))
    fig, ax = figure(7.6, 7.2)
    ax.barh(y, df["var_zwischen"], height=0.62, color=KI)
    ax.barh(y, df["var_ziehung"], left=df["var_zwischen"], height=0.62, color=light(KI, 0.35))
    ax.scatter(df["var_mensch"], y, s=46, color=REAL, edgecolor="white", lw=1.3, zorder=3)
    xmax = df[["var_twin_gesamt", "var_mensch"]].max().max()
    col = xmax + 0.45   # feste Spalte für den Anteil, damit die Zahl nicht wie der Wert des Punkts wirkt
    for yi, r in zip(y, df.itertuples(), strict=True):
        ax.text(col, yi, pct(r.anteil_zwischen), va="center", ha="right", fontsize=8.5, color=INK2)
    ax.text(col, len(df) - 0.2, "Anteil zwischen\nden Twins", ha="right", va="bottom", fontsize=8, color=INK2,
            linespacing=1.2)
    ylabels(ax, y, [item_label(i, qno) for i in df["item"]])
    vgrid(ax)
    comma_axis(ax)
    ax.set_xlim(0, col + 0.02)
    ax.set_ylim(-0.7, len(df) + 0.6)
    ax.set_xticks(np.arange(0, xmax + 0.01, 0.5))
    ax.set_xlabel("Varianz der Antworten über alle Personen (Skalenpunkte²)", loc="left")
    share = df["var_zwischen"].sum() / df["var_twin_gesamt"].sum()
    header(fig, "A2  Woher kommt die Breite der Twins?",
           f"Aus dem Zufall der Ziehung: Nur rund {pct(share)} der Streuung der Twins unterscheidet die Twins "
           "voneinander (kräftig),\nder Rest entsteht erst beim Auslosen der Antworten (blass).",
           keys=[(KI, "zwischen den Twins (Varianz der Erwartungswerte)", "sq"),
                 (light(KI, 0.35), "durch die Ziehung (Varianz innerhalb jedes Twins, seines Wahrscheinlichkeitsvektors)",
                  "sq"),
                 (REAL, "Personen", "dot")], ncol=2,
           footer=footer_text(n, "Wahrscheinlichkeitsvektoren der Twins",
                              "Satz von der totalen Varianz: gezogene Antworten = Erwartungswerte + Ziehung"))
    save(fig, out, "A2_varianzzerlegung")


# ---------------------------------------------------------------------------
# Ebene 2
# ---------------------------------------------------------------------------

def fig_20(ksel: pd.DataFrame, null_sil: pd.DataFrame, null_sil_l: pd.DataFrame, n: int, out: Path) -> None:
    """null_sil / null_sil_l: Zufallsdaten ohne Gruppen nach Vorbild der Personen bzw. der Twins."""
    fig, ax = figure(7.6, 4.6)
    ax.plot(null_sil["k"], null_sil["mean"], color=REF, lw=2, ls="--")
    ax.plot(null_sil_l["k"], null_sil_l["mean"], color=light(KI, 0.5), lw=2, ls="--")
    for who, col in [("mensch", REAL), ("llm", KI)]:
        d = ksel[ksel.daten == who]
        ax.plot(d["k"], d["silhouette"], color=col, lw=2, marker="o", ms=5.5, mec="white", mew=1.2)
    s = ksel.set_index(["daten", "k"])["silhouette"]
    n_l2 = null_sil_l.set_index("k").loc[2, "mean"]
    ax.annotate(f"Twins: {de(s['llm', 2])} (ihre Zufallsdaten {de(n_l2)})", xy=(2, s["llm", 2]),
                xytext=(2.35, s["llm", 2] + 0.012), fontsize=8.5, color=INK, va="center",
                arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})
    ax.set_ylim(0, 0.28)
    ax.set_xlim(1.8, 8.2)
    hgrid(ax)
    comma_axis(ax, "y")
    ax.set_xlabel("Anzahl Gruppen k")
    ax.set_ylabel("Silhouette (0 = keine Trennung, 1 = perfekt)")
    header(fig, "2.0  Gibt es überhaupt getrennte Milieus?",
           "Bei Personen nicht: Ihre Gruppen sind nicht klarer getrennt als in Zufallsdaten ohne Gruppen, ihre Werte "
           "bilden\nein Kontinuum. Die Twins liegen bei k = 2 auch über ihren eigenen Zufallsdaten, sie teilen sich "
           "etwas deutlicher\nin zwei Lager. Für den Vergleich wird k = 2 gesetzt; die Milieus sind Regionen im "
           "Kontinuum.",
           keys=[(REAL, "Personen", "dot"), (KI, "Twins", "dot"),
                 (REF, "Zufallsdaten ohne Gruppen, wie Personen", "dash"),
                 (light(KI, 0.5), "Zufallsdaten ohne Gruppen, wie Twins", "dash")], ncol=2,
           footer=footer_text(n, "10 zentrierte Werte aus gezogenen Antworten · k-Means",
                              "Zufallsdaten: Normalverteilung mit gleicher Streuung\nund gleichen Zusammenhängen wie "
                              "Personen bzw. Twins, Mittel aus 5 Ziehungen · LPA-BIC bevorzugt bei Personen k = 1"))
    save(fig, out, "FF2_0_milieus_existenz")


def fig_21(xy_h: np.ndarray, xy_l: np.ndarray, lab_h: np.ndarray, lab_l: np.ndarray, names: list[str], n: int,
           out: Path) -> None:
    fig, axes = subplots(1, 2, figsize=(10, 6.2), sharex=True, sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, xy, lab, title in [(axes[0], xy_h, lab_h, "Personen"), (axes[1], xy_l, lab_l, "Twins")]:
        ax.axhline(0, color=AXIS, lw=1)
        ax.axvline(0, color=AXIS, lw=1)
        for c in range(2):
            p = xy[lab == c]
            ax.scatter(p[:, 0], p[:, 1], s=4, color=MILIEU[c], alpha=0.22, lw=0)
            m = p.mean(0)
            ax.scatter(*m, s=120, color=MILIEU[c], edgecolor="white", lw=2, zorder=4)
            ax.text(m[0] + 0.25, m[1] + 0.25, f"{names[c]}\n{pct(np.mean(lab == c))}", fontsize=9,
                    fontweight="semibold", color=INK, zorder=5)
        ax.set_title(title, loc="left", fontsize=10.5, color=INK, fontweight="semibold")
        ax.set_aspect("equal")
        ax.set_xlim(-4.5, 5.5)
        ax.set_ylim(-5, 5)
        ax.set_xlabel("← Selbststärkung   ·   Selbsttranszendenz →")
        comma_axis(ax)
        comma_axis(ax, "y")
    axes[0].set_ylabel("← Bewahrung   ·   Offenheit →")
    open_, cons = sorted(names, key=lambda s: "bewahrend" in s)
    header(fig, "2.1  Wo liegen die Milieus im Wertekreis?",
           "Jeder Punkt ist eine Person bzw. ihr Twin, der große Punkt die Mitte des Milieus. "
           f"{open_} liegt oben,\n{cons} unten. Die Twins streuen weiter und rutschen Richtung Bewahrung. "
           "Gebildet aus 10 Werten,\ngezeigt auf 2 Achsen, daher überlappen die Farben.",
           keys=[(MILIEU[c], names[c], "dot") for c in range(2)], extra=0.3,
           footer=footer_text(n, "gezogene Antworten",
                              "Milieus: Latent-Profile-Analyse mit k = 2 auf 10 zentrierten Werten, getrennt für "
                              "Personen und Twins"))
    save(fig, out, "FF2_1_milieus")


def fig_2a(ch: np.ndarray, cl: np.ndarray, share_h, share_l, names: list[str], dist: float, noise: float,
           dist_m: list[float], between_h: float, n: int, out: Path) -> None:
    """between_h = Abstand der beiden Personen-Milieus untereinander: inhaltlicher Maßstab für `dist`."""
    fig, axes = subplots(1, 2, figsize=(10, 5.2), sharey=True, gridspec_kw={"wspace": 0.08})
    x = np.arange(len(BASIC_VALUES))
    for c, ax in enumerate(axes):
        ax.axhline(0, color=AXIS, lw=1)
        ax.plot(x, ch[c], color=REAL, lw=2, marker="o", ms=5.5, mec="white", mew=1.2)
        ax.plot(x, cl[c], color=KI, lw=2, marker="o", ms=5.5, mec="white", mew=1.2)
        ax.set_xticks(x, [VALUE_NAME[v] for v in BASIC_VALUES], rotation=40, ha="right", rotation_mode="anchor")
        hgrid(ax)
        comma_axis(ax, "y")
        ax.set_title(f"{names[c]}\n{pct(share_h[c])} der Personen, {pct(share_l[c])} der Twins  ·  "
                     f"Abstand {de(dist_m[c])}", loc="left", fontsize=9.5, color=INK, fontweight="semibold",
                     linespacing=1.4)
    axes[0].set_ylabel("Zentrierte Wichtigkeit\n(0 = persönlicher Durchschnitt aller Werte)")
    header(fig, "2a  Liegen die Milieus der Twins dort, wo die echten liegen?",
           f"Der Profilverlauf stimmt, die Lage nicht: Die Twins sind um {de(dist)} verschoben, das ist "
           f"{pct(dist / between_h)} des Abstands der beiden\nPersonen-Milieus ({de(between_h)}). Leistung und "
           "Hedonismus liegen bei den Twins tiefer, Konformität höher.",
           keys=[(REAL, "Personen", "dot"), (KI, "Twins", "dot")], extra=0.5,
           footer=footer_text(n, "gezogene Antworten",
                              f"Abstand {de(dist)}: euklidisch zwischen den Mittelpunkten aller Personen und aller "
                              "Twins im 10-dimensionalen Werteraum;\nje Milieu im Panel-Titel · Rauschniveau (Abstand "
                              f"zweier Zufallshälften der Personen): {de(noise)}\nWerte in der Reihenfolge des "
                              "Wertekreises nach Schwartz (Universalismus grenzt wieder an Selbstbestimmung); "
                              "die Linien sind nur Lesehilfe"))
    save(fig, out, "FF2a_lage")


def fig_2b(metr: pd.DataFrame, names: list[str], n: int, out: Path) -> None:
    d = metr.iloc[::-1].reset_index(drop=True)
    y = np.arange(len(d))
    fig, ax = figure(7.6, 4.8)
    bh = 0.24
    ax.barh(y + bh, d["tr_mensch"], height=bh * 0.9, color=REAL)
    ax.barh(y, d["tr_llm"], height=bh * 0.9, color=KI)
    ax.barh(y - bh, d["tr_llm_erwartung"], height=bh * 0.9, color=light(KI, 0.35))
    for yi, r in d.iterrows():
        ax.text(r.tr_mensch + 0.12, yi + bh, de(r.tr_mensch, 1), va="center", fontsize=8.5, color=INK2)
        ax.text(r.tr_llm + 0.12, yi, f"{de(r.tr_llm, 1)}  (× {de(r.tr_verhaeltnis)})", va="center", fontsize=8.5,
                color=INK, fontweight="semibold")
        ax.text(r.tr_llm_erwartung + 0.12, yi - bh, f"{de(r.tr_llm_erwartung, 1)}  "
                f"(× {de(r.tr_verhaeltnis_erwartung)})", va="center", fontsize=8.5, color=INK2)
    label = {"gesamt": "Gesamt", **{f"Milieu {c + 1}": names[c] for c in range(len(names))}}
    ylabels(ax, y, [label[r.gruppe] for r in d.itertuples()])
    ax.set_xlim(0, 12.5)
    vgrid(ax)
    comma_axis(ax)
    ax.set_xlabel("Gesamtstreuung = Summe der Varianzen der 10 Werte")
    g = metr.set_index("gruppe").loc["gesamt"]
    header(fig, "2b  Ist die simulierte Population gleich breit?",
           f"Nein, breiter: Mit gezogenen Antworten streuen die Twins × {de(g.tr_verhaeltnis)} so stark wie die "
           "Personen, auch innerhalb der Milieus.\nDiese Breite stammt aus der Zufallsziehung, nicht aus Unterschieden "
           f"zwischen den Twins: Mit Erwartungswerten sind es nur × {de(g.tr_verhaeltnis_erwartung)}.",
           keys=[(REAL, "Personen", "sq"), (KI, "Twins, gezogene Antworten", "sq"),
                 (light(KI, 0.35), "Twins, Erwartungswerte", "sq")],
           footer=footer_text(n, "Werte aus gezogenen Antworten bzw. Erwartungswerten · Milieus wie in 2.1",
                              "Faktor = Twins / Personen\nAuch die Erwartungswert-Balken je Milieu nutzen die Milieus "
                              "aus den gezogenen Antworten · Summe über die 10 Werte,\ndaher ein anderer Faktor als in "
                              "A2 (Varianz der 21 Fragen)"))
    save(fig, out, "FF2b_streuung")


def fig_2c(xh: np.ndarray, xl: np.ndarray, p: float, n: int, out: Path) -> None:
    fig, axes = subplots(2, 5, figsize=(10.5, 5.6), sharex=True, sharey=True,
                         gridspec_kw={"wspace": 0.12, "hspace": 0.45})
    edges = np.linspace(-4, 3.5, 21)
    alpha = 0.18
    for j, ax in enumerate(axes.ravel()):
        for data, col in [(xh[:, j], REAL), (xl[:, j], KI)]:
            v, _ = np.histogram(data, bins=edges)
            v = v / v.sum()
            ax.stairs(v, edges, color=col, lw=1.6)
            ax.stairs(v, edges, color=col, alpha=alpha, fill=True)
            ax.axvline(data.mean(), color=col, lw=1.3, ls="--")
        ax.axvline(0, color=AXIS, lw=0.8)
        code = BASIC_VALUES[j]
        ax.set_title(f"{VALUE_NAME[code]}", loc="left", fontsize=9.5, color=INK, fontweight="semibold")
        hgrid(ax)
        comma_axis(ax)
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    axes[1, 2].set_xlabel("Zentrierte Wichtigkeit des Werts (0 = persönlicher Durchschnitt aller Werte)")
    axes[0, 0].set_ylabel("Anteil")
    axes[1, 0].set_ylabel("Anteil")
    pt = "p < 0,001" if p < 0.001 else f"p ≤ {de(p, 3)}"
    header(fig, "2c  Haben die Verteilungen dieselbe Form?",
           f"Nein ({pt}). Die Twin-Verteilungen sind breiter, bei Hedonismus und Leistung nach links und bei "
           "Konformität\nnach rechts verschoben.",
           keys=[(REAL, "Personen", "sq"), (KI, "Twins", "sq"),
                 (over_white((REAL, alpha), (KI, alpha)), "Mischfarbe = Überlappung", "sq"),
                 (INK2, "Mittelwert (Farbe je Gruppe)", "dash")], extra=0.3,
           footer=footer_text(n, "gezogene Antworten",
                              "MMD-Permutationstest über alle 10 Werte (500 Vertauschungen), gesamt und je Milieu"))
    save(fig, out, "FF2c_form")


def fig_2d(cont: np.ndarray, same: float, chance: float, ari: float, names: list[str], out: Path) -> None:
    rowp = cont / cont.sum(1, keepdims=True)
    k = len(rowp)
    cmap = LinearSegmentedColormap.from_list("grau", ["#f4f3ee", INK2])   # neutral: Lila steht sonst für Milieu 2
    fig, ax = figure(7.0, 4.8)
    ax.imshow(rowp, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(k):
        for j in range(k):
            dark = rowp[i, j] > 0.55
            ax.text(j, i - 0.06, pct(rowp[i, j]), ha="center", va="center", fontsize=13,
                    fontweight="semibold", color="white" if dark else INK)
            ax.text(j, i + 0.22, f"{num(int(cont[i, j]))} Personen", ha="center", va="center", fontsize=8,
                    color="white" if dark else INK2)
        ax.text(k, i, num(int(cont[i].sum())), ha="center", va="center", fontsize=10, color=INK2)
    for j in range(k):
        ax.text(j, k, num(int(cont[:, j].sum())), ha="center", va="center", fontsize=10, color=INK2)
    ax.text(k, k, num(int(cont.sum())), ha="center", va="center", fontsize=10, color=INK, fontweight="semibold")
    ax.set_xlim(-0.5, k + 0.5)
    ax.set_ylim(k + 0.5, -0.5)
    ax.axhline(k - 0.5, color=AXIS, lw=1)
    ax.axvline(k - 0.5, color=AXIS, lw=1)
    ax.set_xticks(range(k + 1), [f"Twin in\n{nm}" for nm in names] + ["Summe"])
    ax.set_yticks(range(k + 1), [f"Person in\n{nm}" for nm in names] + ["Summe"])
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_color(INK2)
        lab.set_fontsize(9)
    ax.xaxis.tick_top()
    col_share = cont.sum(0) / cont.sum()   # Trefferquote je Zeile bei zufälliger Zuordnung = Anteil der Twins
    header(fig, "2d  Landet der Twin im Milieu seiner Person?",
           f"Kaum öfter als per Zufall: {pct(same)} Treffer, erwartet bei zufälliger Zuordnung {pct(chance)} "
           f"(ARI {de(ari)}). In beiden Milieus\nnur gut 10 Punkte über dem Zufall: {names[0]} {pct(rowp[0, 0])} "
           f"(Zufall {pct(col_share[0])}), {names[1]} {pct(rowp[1, 1])} (Zufall {pct(col_share[1])}).",
           extra=0.45,
           footer=f"N = {num(int(cont.sum()))} Paare aus Person und Twin · gezogene Antworten · Zeilen = Milieu "
                  "der Person, Spalten = Milieu des Twins, Diagonale = Treffer\nProzent und Farbe = Anteil an der "
                  "Zeile · Zufall je Zeile = Anteil der Twins im Milieu (Spaltensumme / N)\nARI = Übereinstimmung "
                  "der Gruppierung, um Zufall bereinigt (0 = Zufall, 1 = perfekt)")
    save(fig, out, "FF2d_zuordnung")


def fig_fazit3(r2df: pd.DataFrame, n: int, out: Path) -> None:
    """Twins in beiden Varianten: gezogene Antworten (Ziehungsrauschen drückt R², untere Schranke) und
    Erwartungswerte (entrauscht gegen Personen mit Messfehler, obere Schranke). Faktor je Variante rechts."""
    df = r2df[r2df.wert.isin(BASIC_VALUES)].sort_values("r2_llm_erwartung").reset_index(drop=True)
    y = np.arange(len(df))
    fig, ax = figure(7.6, 5.4)
    top_h = df["r2_mensch"].max()
    ax.axvline(top_h, color=REAL, lw=1, ls=":", zorder=0)
    ax.text(top_h + 0.004, len(df) - 0.45, f"höchster Wert der Personen ({pct(top_h)})", fontsize=8, color=REAL,
            va="bottom")
    ax.hlines(y, df["r2_mensch"], df["r2_llm_erwartung"], color=AXIS, lw=2, zorder=1)
    ax.scatter(df["r2_mensch"], y, s=58, color=REAL, edgecolor="white", lw=1.5, zorder=3)
    ax.scatter(df["r2_llm"], y, s=58, color=KI, edgecolor="white", lw=1.5, zorder=3)
    ax.scatter(df["r2_llm_erwartung"], y, s=50, facecolor="white", edgecolor=KI, lw=1.8, zorder=3)
    f_e, f_g = df.r2_llm_erwartung / df.r2_mensch, df.r2_llm / df.r2_mensch
    c_g, c_e = df["r2_llm_erwartung"].max() + 0.12, df["r2_llm_erwartung"].max() + 0.22   # Spalten für die Faktoren
    for yi in y:
        sure_g = df.faktor_gezogen_ci_unten[yi] > 1   # 95-%-Bootstrap-Intervall des Faktors über 1
        ax.text(c_g, yi, f"× {de(f_g[yi], 1)}" + ("" if sure_g else "*"), va="center", ha="right", fontsize=8.5,
                color=INK2 if sure_g else MUTED)
        ax.text(c_e, yi, f"× {de(f_e[yi], 1)}", va="center", ha="right", fontsize=8.5, color=INK, fontweight="semibold")
    ax.text(c_g, len(df) - 0.45, "gezogen", ha="right", va="bottom", fontsize=8, color=INK2)
    ax.text(c_e, len(df) - 0.45, "Erw.-Wert", ha="right", va="bottom", fontsize=8, color=INK, fontweight="semibold")
    ylabels(ax, y, [VALUE_NAME[v] for v in df["wert"]])
    ax.set_xlim(0, c_e + 0.01)
    ax.set_xticks(np.arange(0, df["r2_llm_erwartung"].max() + 0.01, 0.1))
    ax.set_ylim(-0.6, len(df) - 0.1)
    vgrid(ax)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xlabel("Von der Demografie erklärter Anteil der Unterschiede zwischen Personen (R²)", loc="left")
    # Rangfolge nach Abstand in Prozentpunkten: stabiler als der Quotient, dessen Nenner (R² der Personen) klein ist
    t3 = [VALUE_NAME[v] for v in df.assign(d=df.r2_llm_erwartung - df.r2_mensch).sort_values("d", ascending=False)
          .head(3).wert]
    header(fig, "Fazit 3  Spiegeln die Twins Werte oder Demografie?",
           "Eher Demografie: Geschlecht, Alter, Bildung, Wohnort, Region und Religion erklären bei den Twins mehr "
           f"Wertevarianz\nals bei Personen: gezogen × {de(f_g.min(), 1)}–{de(f_g.max(), 1)}, mit Erwartungswerten "
           f"× {de(f_e.min(), 1)}–{de(f_e.max(), 1)}; der größte Abstand bei {t3[0]}, {t3[1]} und {t3[2]}.",
           keys=[(REAL, "Person", "dot"), (KI, "Twin, gezogene Antworten", "dot"),
                 (KI, "Twin, Erwartungswerte", "ring")],
           footer=footer_text(n, "mit vollständigen Angaben",
                              "lineare Regression je Wert auf sechs Merkmale (Dummy-kodiert)\n"
                              "Gezogen = untere Schranke (Ziehungsrauschen ist nicht demografisch erklärbar); "
                              "Erwartungswerte = obere Schranke (entrauschte Twins gegen\nPersonen mit Messfehler). "
                              "Die sechs Merkmale stehen selbst im Profil des Twins: Ein hoher R² ist zum Teil "
                              "konstruktionsbedingt.\n* 95-%-Bootstrap-Intervall des Faktors schließt 1 ein (500 Stichproben, "
                              "Intervalle in demografie_r2.csv); die Faktoren sind Quotienten kleiner R² und schwanken."))
    save(fig, out, "Fazit3_werte_oder_demografie")
