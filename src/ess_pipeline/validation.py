"""
Phase 2 – Validierung der Score-Berechnung und von ess_scores.csv (Prüfungen A–D).

`run_validation` erzeugt ess_scores.csv neu (zwischen zwei SHA-256-Hashes der
Eingabedateien), führt alle 18 Prüfungen aus, gibt den Prüfbericht auf der
Konsole aus und schreibt ihn zusätzlich als validation_report.txt.
"""

from __future__ import annotations

import csv
import random
import traceback
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import pandas as pd

from . import scoring as cs
from .csv_io import sha256

ID = "id"
TOL = 1e-9
SEED = 20261014
N_SAMPLE = 50

# Unabhängig von scoring.py abgeschrieben aus der Aufgabenbeschreibung
REF_ITEMS = {
    "SD": ["ipcrtiva", "impfreea"],
    "ST": ["impdiffa", "ipadvnta"],
    "HE": ["ipgdtima", "impfuna"],
    "AC": ["ipshabta", "ipsucesa"],
    "PO": ["impricha", "iprspota"],
    "SE": ["impsafea", "ipstrgva"],
    "CO": ["ipfrulea", "ipbhprpa"],
    "TR": ["ipmodsta", "imptrada"],
    "BE": ["iphlppla", "iplylfra"],
    "UN": ["ipeqopta", "ipudrsta", "impenva"],
}
REF_HO_ITEMS = {
    "OPEN": ["ipcrtiva", "impfreea", "impdiffa", "ipadvnta", "ipgdtima", "impfuna"],
    "CONS": ["impsafea", "ipstrgva", "ipfrulea", "ipbhprpa", "ipmodsta", "imptrada"],
    "SELFENH": ["ipshabta", "ipsucesa", "impricha", "iprspota"],
    "SELFTRANS": ["ipeqopta", "ipudrsta", "impenva", "iphlppla", "iplylfra"],
}
# Higher-Order Value = ungewichtetes Mittel dieser Basiswerte
REF_HO_BV = {
    "OPEN": ["SD", "ST", "HE"],
    "CONS": ["SE", "CO", "TR"],
    "SELFENH": ["AC", "PO"],
    "SELFTRANS": ["UN", "BE"],
}
ALL_ITEMS = [i for v in REF_ITEMS.values() for i in v]
EXPECTED_COLUMNS = [ID, "MRAT", "SD", "ST", "HE", "AC", "PO", "SE", "CO", "TR", "BE", "UN",
                    "OPEN", "CONS", "SELFENH", "SELFTRANS", "x", "y"]
SCORE_COLS = EXPECTED_COLUMNS[1:]


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def read_ids(path: Path) -> list[str]:
    return pd.read_csv(path, dtype=str, usecols=[ID])[ID].tolist()


def simple_scores(raw: dict[str, int]) -> dict[str, float]:
    """Bewusst einfache, schleifenbasierte Referenzimplementierung (default hedonism_to='openness')."""
    rev = {}
    for item in ALL_ITEMS:
        rev[item] = 7 - int(raw[item])
    total = 0.0
    for item in ALL_ITEMS:
        total += rev[item]
    mrat = total / 21
    res = {"MRAT": mrat}
    for bv, items in REF_ITEMS.items():
        s = 0.0
        for item in items:
            s += rev[item]
        res[bv] = s / len(items) - mrat
    for ho, bvs in REF_HO_BV.items():
        s = 0.0
        for bv in bvs:
            s += res[bv]
        res[ho] = s / len(bvs)
    res["x"] = res["SELFTRANS"] - res["SELFENH"]
    res["y"] = res["OPEN"] - res["CONS"]
    return res


class Report:
    def __init__(self):
        self.lines: list[str] = []
        self.results: list[tuple[str, str]] = []

    def log(self, text: str = ""):
        print(text)
        self.lines.append(text)

    def run(self, name: str, fn, warn_only: bool = False):
        """fn gibt optional Detailtext zurück; AssertionError = Fehlschlag (bzw. Warnung)."""
        try:
            details = fn()
            status = "BESTANDEN"
        except AssertionError as e:
            details = str(e)
            status = "WARNUNG" if warn_only else "FEHLGESCHLAGEN"
        except Exception:
            details = traceback.format_exc()
            status = "FEHLGESCHLAGEN"
        self.results.append((name, status))
        self.log(f"[{status:^14}] {name}")
        if details:
            for line in str(details).rstrip().splitlines():
                self.log(f"                 {line}")


# ---------------------------------------------------------------------------
# Lauf
# ---------------------------------------------------------------------------

def run_validation(profile_csv: str | Path, quest_csv: str | Path, scores_csv: str | Path,
                   report_txt: str | Path) -> int:
    """Gibt die Anzahl fehlgeschlagener Prüfungen zurück (0 = alles bestanden)."""
    PROFILE_CSV, QUEST_CSV = Path(profile_csv), Path(quest_csv)
    SCORES_CSV, REPORT_TXT = Path(scores_csv), Path(report_txt)
    rep = Report()
    rep.log("=" * 78)
    rep.log("PRÜFBERICHT ess_scores.csv")
    rep.log(f"Profil:     {PROFILE_CSV.name}")
    rep.log(f"Fragebogen: {QUEST_CSV.name}")
    rep.log(f"Scores:     {SCORES_CSV.name}   (hedonism_to='openness')")
    rep.log("=" * 78)

    # Hash vor dem Lauf, Scoring, Hash nach dem Lauf
    hash_before = {p.name: sha256(p) for p in (PROFILE_CSV, QUEST_CSV)}
    cs.run_scoring(QUEST_CSV, SCORES_CSV, hedonism_to="openness")
    hash_after = {p.name: sha256(p) for p in (PROFILE_CSV, QUEST_CSV)}

    profile_ids = read_ids(PROFILE_CSV)
    quest = pd.read_csv(QUEST_CSV, dtype={ID: str})
    scores = pd.read_csv(SCORES_CSV, dtype={ID: str}, float_precision="round_trip")

    # ---------------- A. Struktur und ID-Integrität ----------------
    rep.log("\nA. Struktur und ID-Integrität")

    def t1():
        n = {"Profil": len(profile_ids), "Fragebogen": len(quest), "Scores": len(scores)}
        assert len(set(n.values())) == 1, f"Zeilenzahlen ungleich: {n}"
        return f"je {len(scores)} Zeilen"

    def t2():
        dups = {}
        for name, ids in (("Profil", profile_ids), ("Fragebogen", quest[ID].tolist()), ("Scores", scores[ID].tolist())):
            s = pd.Series(ids)
            d = s[s.duplicated()].unique().tolist()
            if d:
                dups[name] = d
        assert not dups, f"Doppelte IDs: {dups}"

    def t3():
        sets = {"Profil": set(profile_ids), "Fragebogen": set(quest[ID]), "Scores": set(scores[ID])}
        msgs = []
        names = list(sets)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                if sets[a] - sets[b]:
                    msgs.append(f"nur in {a}, nicht in {b}: {sorted(sets[a] - sets[b])}")
                if sets[b] - sets[a]:
                    msgs.append(f"nur in {b}, nicht in {a}: {sorted(sets[b] - sets[a])}")
        assert not msgs, "\n".join(msgs)

    def t4():
        a, b = quest[ID].to_numpy(), scores[ID].to_numpy()
        assert len(a) == len(b), "unterschiedliche Länge"
        diff = np.flatnonzero(a != b)
        assert diff.size == 0, f"{diff.size} Positionen abweichend, erste: {diff[:10].tolist()}"

    def t5():
        changed = [n for n in hash_before if hash_before[n] != hash_after[n]]
        assert not changed, f"Eingabedatei verändert: {changed}"
        return "\n".join(f"{n}: {h[:16]}…" for n, h in hash_after.items())

    def t6():
        assert list(scores.columns) == EXPECTED_COLUMNS, f"Spalten: {list(scores.columns)}"
        n_nan = int(scores.isna().sum().sum())
        assert n_nan == 0, f"{n_nan} NaN-Werte"
        return f"{len(scores.columns)} Spalten, keine NaN"

    rep.run("1  Gleiche Zeilenzahl (Profil, Fragebogen, Scores)", t1)
    rep.run("2  Eindeutige IDs in allen drei Dateien", t2)
    rep.run("3  Identische ID-Mengen", t3)
    rep.run("4  Gleiche ID-Reihenfolge Scores == Fragebogen", t4)
    rep.run("5  Eingaben unverändert (SHA-256 vor/nach Lauf)", t5)
    rep.run("6  Vollständigkeit (18 Spalten, keine NaN)", t6)

    # ---------------- B. Eingabevalidierung ----------------
    rep.log("\nB. Eingabevalidierung")

    def t7():
        missing = [c for c in ALL_ITEMS if c not in quest.columns]
        assert not missing, f"Fehlende Item-Spalten in Fragebogen-CSV: {missing}"
        broken = quest.drop(columns=["impfuna"])
        try:
            cs.compute_scores(broken)
        except cs.InputValidationError as e:
            assert "impfuna" in str(e), f"Fehlermeldung nennt Spalte nicht: {e}"
        else:
            raise AssertionError("Fehlende Spalte wurde nicht als Fehler erkannt")
        return "alle 21 Spalten vorhanden; fehlende Spalte -> Fehler"

    def t8():
        vals = quest[ALL_ITEMS]
        ok = vals.notna() & vals.isin([1, 2, 3, 4, 5, 6])
        bad_ids = quest.loc[~ok.all(axis=1), ID].tolist()
        assert not bad_ids, f"Ungültige Werte bei IDs: {bad_ids}"
        # Negativtest: ungültige Werte müssen einen Fehler mit den IDs liefern
        broken = pd.read_csv(QUEST_CSV, dtype=str)
        bad = {0: ("ipcrtiva", "7"), 1: ("impricha", ""), 2: ("impenva", "2.5"), 3: ("ipfrulea", "0")}
        for row, (col, v) in bad.items():
            broken.at[row, col] = v
        try:
            cs.compute_scores(broken)
        except cs.InputValidationError as e:
            for row in bad:
                assert broken.at[row, ID] in str(e), f"ID {broken.at[row, ID]} fehlt in Fehlermeldung"
        else:
            raise AssertionError("Ungültige Werte wurden nicht als Fehler erkannt")
        return "alle Werte ganzzahlig 1–6; Werte 7 / leer / 2.5 / 0 -> Fehler mit IDs"

    rep.run("7  Alle 21 Item-Spalten vorhanden (sonst Fehler)", t7)
    rep.run("8  Item-Werte ganzzahlig in {1..6}, keine leeren Zellen", t8)

    # ---------------- C. Rechenkorrektheit ----------------
    rep.log("\nC. Rechenkorrektheit")

    def t9():
        with open(QUEST_CSV, newline="", encoding="utf-8") as f:
            by_id = {row[ID]: row for row in csv.DictReader(f)}
        score_by_id = scores.set_index(ID)
        sample = random.Random(SEED).sample(sorted(by_id), N_SAMPLE)
        errors = []
        max_dev = 0.0
        for pid in sample:
            ref = simple_scores(by_id[pid])
            got = score_by_id.loc[pid]
            for col in SCORE_COLS:
                d = abs(ref[col] - float(got[col]))
                max_dev = max(max_dev, d)
                if d > TOL:
                    errors.append(f"{pid} {col}: erwartet {ref[col]}, Scores {got[col]}")
        assert not errors, "\n".join(errors[:20])
        return f"{N_SAMPLE} IDs (Seed {SEED}), max. Abweichung {max_dev:.2e}"

    def t10():
        m = quest.merge(scores, on=ID, how="inner", validate="one_to_one")
        assert len(m) == len(scores), f"Merge-Zeilen {len(m)} != {len(scores)}"
        rev = 7 - m[ALL_ITEMS].to_numpy(dtype=float)
        col = {c: k for k, c in enumerate(ALL_ITEMS)}
        mrat = rev.mean(axis=1)
        exp = {"MRAT": mrat}
        for name, items in REF_ITEMS.items():
            exp[name] = rev[:, [col[i] for i in items]].mean(axis=1) - mrat
        for ho, bvs in REF_HO_BV.items():
            exp[ho] = sum(exp[bv] for bv in bvs) / len(bvs)
        exp["x"] = exp["SELFTRANS"] - exp["SELFENH"]
        exp["y"] = exp["OPEN"] - exp["CONS"]
        devs = {c: float(np.max(np.abs(exp[c] - m[c].to_numpy()))) for c in SCORE_COLS}
        bad = {c: d for c, d in devs.items() if d > TOL}
        assert not bad, f"Abweichungen: {bad}"
        return f"{len(m)} Zeilen gemergt, max. Abweichung {max(devs.values()):.2e}"

    def t11():
        s = sum(2 * scores[c] for c in ["SD", "ST", "HE", "AC", "PO", "SE", "CO", "TR", "BE"]) + 3 * scores["UN"]
        worst = float(s.abs().max())
        assert worst <= TOL, f"max |Summe| = {worst}; IDs: {scores.loc[s.abs() > TOL, ID].tolist()[:20]}"
        return f"max |2·SD+…+2·BE+3·UN| = {worst:.2e}"

    def t12():
        ctrl = {
            "OPEN": (scores.SD + scores.ST + scores.HE) / 3,
            "CONS": (scores.SE + scores.CO + scores.TR) / 3,
            "SELFENH": (scores.AC + scores.PO) / 2,
            "SELFTRANS": (scores.UN + scores.BE) / 2,
        }
        msgs, info = [], []
        for ho, c in ctrl.items():
            d = (scores[ho] - c).abs()
            info.append(f"{ho}: max. Abweichung {d.max():.2e}")
            if d.max() > TOL:
                hint = ""
                if np.allclose((c - scores[ho]).to_numpy(), scores.MRAT.to_numpy(), atol=1e-6):
                    hint = " (Abweichung ≈ MRAT -> doppelt zentriert!)"
                msgs.append(f"{ho} weicht ab, max {d.max()}{hint}")
        dx = (scores.x - (scores.SELFTRANS - scores.SELFENH)).abs().max()
        dy = (scores.y - (scores.OPEN - scores.CONS)).abs().max()
        info.append(f"x: {dx:.2e}, y: {dy:.2e}")
        if dx > TOL:
            msgs.append(f"x != SELFTRANS − SELFENH (max {dx})")
        if dy > TOL:
            msgs.append(f"y != OPEN − CONS (max {dy})")
        assert not msgs, "\n".join(msgs)
        return "\n".join(info)

    def t13():
        q = quest.set_index(ID).loc[scores[ID]]
        exp = 7 - q[ALL_ITEMS].mean(axis=1).to_numpy()
        d = float(np.max(np.abs(exp - scores.MRAT.to_numpy())))
        assert d <= TOL, f"max. Abweichung {d}"
        return f"max. Abweichung {d:.2e}"

    def t14():
        info = []
        # (a) Konstante Antworten -> alle 14 Scores, x, y = 0
        for v in range(1, 7):
            df = pd.DataFrame([{ID: f"CONST_{v}", **{i: v for i in ALL_ITEMS}}])
            r = cs.compute_scores(df).iloc[0]
            assert abs(r.MRAT - (7 - v)) <= TOL, f"MRAT bei konstant {v}: {r.MRAT}"
            nz = {c: r[c] for c in SCORE_COLS[1:] if abs(r[c]) > TOL}
            assert not nz, f"konstant {v}: nicht-null Scores {nz}"
        info.append("konstante Antworten 1..6 -> alle Scores, x, y = 0")

        # (b) Handgerechnete Beispielperson
        raw = {
            "ipcrtiva": 1, "impfreea": 1,      # SD -> 6, 6
            "impdiffa": 2, "ipadvnta": 2,      # ST -> 5, 5
            "ipgdtima": 3, "impfuna": 3,       # HE -> 4, 4
            "ipshabta": 4, "ipsucesa": 4,      # AC -> 3, 3
            "impricha": 6, "iprspota": 6,      # PO -> 1, 1
            "impsafea": 2, "ipstrgva": 2,      # SE -> 5, 5
            "ipfrulea": 3, "ipbhprpa": 3,      # CO -> 4, 4
            "ipmodsta": 5, "imptrada": 5,      # TR -> 2, 2
            "iphlppla": 1, "iplylfra": 1,      # BE -> 6, 6
            "ipeqopta": 1, "ipudrsta": 1, "impenva": 4,  # UN -> 6, 6, 3
        }
        # Summe umgepolt = 87 -> MRAT = 87/21 = 29/7
        m = F(29, 7)
        expected = {
            "MRAT": m,
            "SD": 6 - m, "ST": 5 - m, "HE": 4 - m, "AC": 3 - m, "PO": 1 - m,
            "SE": 5 - m, "CO": 4 - m, "TR": 2 - m, "BE": 6 - m, "UN": 5 - m,
            "OPEN": F(6, 7),          # 30/6 − 29/7
            "CONS": F(-10, 21),       # 22/6 − 29/7
            "SELFENH": F(-15, 7),     # 8/4 − 29/7
            "SELFTRANS": F(19, 14),   # (UN + BE)/2 = 11/2 − 29/7
            "x": F(7, 2),             # 19/14 + 15/7 = 3.5
            "y": F(4, 3),             # 6/7 + 10/21
        }
        df = pd.DataFrame([{ID: "HAND_1", **raw}])
        r = cs.compute_scores(df).iloc[0]
        bad = {c: (float(e), r[c]) for c, e in expected.items() if abs(r[c] - float(e)) > TOL}
        assert not bad, f"Handrechnung weicht ab: {bad}"
        info.append("Handgerechnete Person (MRAT = 29/7, x = 3.5, y = 4/3) exakt getroffen")

        # (c) hedonism_to-Varianten
        imap = cs.ESS_ITEM_MAP
        he = set(REF_ITEMS["HE"])
        base_open = set(REF_ITEMS["SD"] + REF_ITEMS["ST"])
        base_enh = set(REF_ITEMS["AC"] + REF_ITEMS["PO"])
        expected_sets = {
            "openness": {"OPEN": base_open | he, "SELFENH": base_enh},
            "both": {"OPEN": base_open | he, "SELFENH": base_enh | he},
            "none": {"OPEN": base_open, "SELFENH": base_enh},
        }
        for opt, exp_sets in expected_sets.items():
            hoi = cs.higher_order_items(imap, opt)
            for ho, s in exp_sets.items():
                assert set(hoi[ho]) == s and len(hoi[ho]) == len(s), f"{opt}/{ho}: {hoi[ho]}"
            assert set(hoi["CONS"]) == set(REF_HO_ITEMS["CONS"])
            assert set(hoi["SELFTRANS"]) == set(REF_HO_ITEMS["SELFTRANS"])
        r_both = cs.compute_scores(df, hedonism_to="both").iloc[0]
        r_none = cs.compute_scores(df, hedonism_to="none").iloc[0]
        checks = {
            ("both", "OPEN"): F(6, 7),
            ("both", "SELFENH"): F(8, 3) - m,                     # (AC + PO + HE)/3 = (3+1+4)/3 − MRAT
            ("none", "OPEN"): F(11, 2) - m,                       # (SD + ST)/2 = (6+5)/2 − MRAT
            ("none", "SELFENH"): F(-15, 7),
        }
        rows = {"both": r_both, "none": r_none}
        for (opt, ho), e in checks.items():
            assert abs(rows[opt][ho] - float(e)) <= TOL, f"{opt}/{ho}: {rows[opt][ho]} != {float(e)}"
        # Kontrollformeln der Varianten auf echten Daten
        sb = cs.compute_scores(quest, hedonism_to="both")
        sn = cs.compute_scores(quest, hedonism_to="none")
        assert ((sb.SELFENH - (sb.AC + sb.PO + sb.HE) / 3).abs().max()) <= TOL, "both: SELFENH != (AC+PO+HE)/3"
        assert ((sn.OPEN - (sn.SD + sn.ST) / 2).abs().max()) <= TOL, "none: OPEN != (SD+ST)/2"
        try:
            cs.compute_scores(df, hedonism_to="foo")
        except ValueError:
            pass
        else:
            raise AssertionError("ungültiges hedonism_to wurde akzeptiert")
        info.append("hedonism_to: openness (OPEN 6 / SELFENH 4 Items), both (6 / 6), none (4 / 4) korrekt")
        return "\n".join(info)

    rep.run("9  Unabhängige Zweitberechnung per ID (50 Stichproben, Schleife)", t9)
    rep.run("10 Merge-Test (Fragebogen ⋈ Scores per ID, Neuberechnung)", t10)
    rep.run("11 Summen-Identität 2·SD+…+2·BE+3·UN = 0", t11)
    rep.run("12 Higher-Order ↔ Kontrollformeln, x/y-Koordinaten", t12)
    rep.run("13 MRAT = 7 − Zeilenmittel der Roh-Items", t13)
    rep.run("14 Synthetische Testfälle (konstant, Handrechnung, hedonism_to)", t14)

    # ---------------- D. Plausibilität ----------------
    rep.log("\nD. Plausibilität (Warnung statt Abbruch)")

    def t15():
        centered = SCORE_COLS[1:]
        msgs = []
        mr = scores.MRAT
        if not mr.between(1, 6).all():
            msgs.append(f"MRAT außerhalb [1, 6]: {scores.loc[~mr.between(1, 6), ID].tolist()[:20]}")
        out5 = (scores[centered].abs() > 5).sum()
        if out5.sum():
            msgs.append(f"Werte außerhalb [−5, 5]: {out5[out5 > 0].to_dict()}")
        out3 = (scores[centered].abs() > 3).sum()
        info = (f"MRAT-Bereich [{mr.min():.3f}, {mr.max():.3f}]\n"
                f"Auffälligkeiten |Wert| > 3: {int(out3.sum())} Zellen "
                f"({int((scores[centered].abs() > 3).any(axis=1).sum())} Personen)"
                + (f": {out3[out3 > 0].to_dict()}" if out3.sum() else ""))
        assert not msgs, "\n".join(msgs + [info])
        return info

    def t16():
        means = scores[cs.BASIC_VALUES].mean().sort_values(ascending=False)
        rank = {v: i + 1 for i, v in enumerate(means.index)}
        txt = "Rangfolge: " + ", ".join(f"{v} {means[v]:+.3f}" for v in means.index)
        msgs = []
        if rank["BE"] > 3:
            msgs.append(f"BE nur auf Rang {rank['BE']}")
        if rank["UN"] > 3:
            msgs.append(f"UN nur auf Rang {rank['UN']}")
        if rank["PO"] < 8:
            msgs.append(f"PO auf Rang {rank['PO']} (erwartet unter den niedrigsten)")
        assert not msgs, "\n".join(msgs + [txt, "-> Umpolen prüfen!"])
        return txt

    def t17():
        r1 = scores.OPEN.corr(scores.CONS)
        r2 = scores.SELFENH.corr(scores.SELFTRANS)
        txt = f"r(OPEN, CONS) = {r1:+.4f}\nr(SELFENH, SELFTRANS) = {r2:+.4f}"
        assert r1 < 0 and r2 < 0, "Korrelation nicht negativ\n" + txt
        return txt

    def t18():
        desc = scores[SCORE_COLS].agg(["count", "mean", "std", "min", "max"]).T
        desc.columns = ["n", "Mittel", "SD", "Min", "Max"]
        desc["n"] = desc["n"].astype(int)
        return desc.to_string(float_format=lambda v: f"{v:+.4f}")

    rep.run("15 Wertebereiche (MRAT in [1,6], Scores in [−5,5], Auffälligkeiten > |3|)", t15, warn_only=True)
    rep.run("16 Wertehierarchie (BE, UN oben; PO unten)", t16, warn_only=True)
    rep.run("17 Erwartete Gegensätze (negative Korrelationen)", t17, warn_only=True)
    rep.run("18 Zusammenfassung", t18, warn_only=True)

    # ---------------- Zusammenfassung ----------------
    n_ok = sum(s == "BESTANDEN" for _, s in rep.results)
    n_fail = sum(s == "FEHLGESCHLAGEN" for _, s in rep.results)
    n_warn = sum(s == "WARNUNG" for _, s in rep.results)
    rep.log("\n" + "=" * 78)
    rep.log(f"ERGEBNIS: {n_ok} bestanden, {n_fail} fehlgeschlagen, {n_warn} Warnungen "
            f"(von {len(rep.results)} Tests)")
    rep.log("=" * 78)

    REPORT_TXT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_TXT.write_text("\n".join(rep.lines) + "\n", encoding="utf-8")
    return n_fail

