"""
Phase 2 – Berechnung der 10 Schwartz-Basiswerte, 4 Higher-Order Values und der
x/y-Koordinaten im Wertekreis aus PVQ-21-Antworten.

Die Funktion `compute_scores` ist datensatzunabhängig: Item-Mapping,
ID-Spaltenname, Skala und Hedonism-Zuordnung werden als Parameter übergeben,
damit sie später unverändert auf die LLM-Antworten (Silicon Samples)
angewendet werden kann. Die ESS-Konfiguration liegt in `config.py`.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import ESS_ITEM_MAP
from .config import ID_COL as ESS_ID_COL

BASIC_VALUES = ["SD", "ST", "HE", "AC", "PO", "SE", "CO", "TR", "BE", "UN"]
HIGHER_ORDER = ["OPEN", "CONS", "SELFENH", "SELFTRANS"]
SCORE_COLUMNS = ["MRAT"] + BASIC_VALUES + HIGHER_ORDER + ["x", "y"]

HEDONISM_OPTIONS = ("openness", "both", "none")


class InputValidationError(ValueError):
    """Eingabedaten entsprechen nicht den Erwartungen."""


# ---------------------------------------------------------------------------
# Higher-Order-Definition
# ---------------------------------------------------------------------------

def higher_order_basic_values(hedonism_to: str = "openness") -> dict[str, list[str]]:
    """Welche Basiswerte gehören zu welchem Higher-Order Value."""
    if hedonism_to not in HEDONISM_OPTIONS:
        raise ValueError(f"hedonism_to muss eines von {HEDONISM_OPTIONS} sein, nicht {hedonism_to!r}")
    open_ = ["SD", "ST"] + (["HE"] if hedonism_to in ("openness", "both") else [])
    selfenh = ["AC", "PO"] + (["HE"] if hedonism_to == "both" else [])
    return {
        "OPEN": open_,
        "CONS": ["SE", "CO", "TR"],
        "SELFENH": selfenh,
        "SELFTRANS": ["UN", "BE"],
    }


def higher_order_items(item_map: dict[str, list[str]], hedonism_to: str = "openness") -> dict[str, list[str]]:
    """Items, die über ihre Basiswerte zu einem Higher-Order Value gehören (Dokumentation/Tests)."""
    return {
        ho: [item for bv in bvs for item in item_map[bv]]
        for ho, bvs in higher_order_basic_values(hedonism_to).items()
    }


# ---------------------------------------------------------------------------
# Eingabevalidierung
# ---------------------------------------------------------------------------

def validate_input(df: pd.DataFrame, item_map: dict[str, list[str]], id_col: str,
                   scale_min: int = 1, scale_max: int = 6) -> pd.DataFrame:
    """Prüft Spalten, IDs und Wertebereich; gibt die Items als int-DataFrame (Index = ID) zurück."""
    if set(item_map) != set(BASIC_VALUES):
        raise InputValidationError(f"item_map muss genau die Basiswerte {BASIC_VALUES} enthalten")
    items = [i for bv in BASIC_VALUES for i in item_map[bv]]
    if len(items) != len(set(items)):
        raise InputValidationError("Ein Item ist mehreren Basiswerten zugeordnet")

    missing_cols = [c for c in [id_col] + items if c not in df.columns]
    if missing_cols:
        raise InputValidationError(f"Fehlende Spalten in der Eingabe: {missing_cols}")

    ids = df[id_col]
    if ids.isna().any() or (ids.astype(str).str.strip() == "").any():
        raise InputValidationError("Leere IDs in der Eingabe")
    dup = ids[ids.duplicated(keep=False)].unique().tolist()
    if dup:
        raise InputValidationError(f"Doppelte IDs: {dup}")

    raw = df[items].copy()
    numeric = raw.apply(lambda s: pd.to_numeric(s.astype(str).str.strip(), errors="coerce"))  # "" -> NaN
    bad = numeric.isna() | (numeric != np.floor(numeric)) | (numeric < scale_min) | (numeric > scale_max)
    if bad.to_numpy().any():
        bad_rows = bad.any(axis=1)
        details = {
            str(ids[r]): {c: raw.at[r, c] for c in items if bad.at[r, c]}
            for r in bad.index[bad_rows]
        }
        raise InputValidationError(
            f"Ungültige Item-Werte (erlaubt: ganzzahlig {scale_min}–{scale_max}, keine leeren Zellen) "
            f"bei {int(bad_rows.sum())} Person(en): {details}"
        )
    numeric = numeric.astype(int)
    numeric.index = ids.astype(str).to_numpy()
    numeric.index.name = id_col
    return numeric


# ---------------------------------------------------------------------------
# Berechnung
# ---------------------------------------------------------------------------

def compute_scores(df: pd.DataFrame, item_map: dict[str, list[str]] = ESS_ITEM_MAP,
                   id_col: str = ESS_ID_COL, hedonism_to: str = "openness",
                   scale_min: int = 1, scale_max: int = 6) -> pd.DataFrame:
    """
    Berechnet MRAT, 10 Basiswerte, 4 Higher-Order Values sowie x/y.

    Rückgabe: DataFrame mit Spalten [id_col] + SCORE_COLUMNS, Zeilenreihenfolge wie `df`.
    """
    raw = validate_input(df, item_map, id_col, scale_min, scale_max)
    items = [i for bv in BASIC_VALUES for i in item_map[bv]]

    # Stufe 1: umpolen (bei 1–6: x' = 7 − x)
    rev = (scale_min + scale_max) - raw[items].astype(float)

    # Stufe 2: MRAT
    mrat = rev.mean(axis=1)

    out = pd.DataFrame(index=raw.index)
    out["MRAT"] = mrat

    # Stufe 3: Basiswerte
    for bv in BASIC_VALUES:
        out[bv] = rev[item_map[bv]].mean(axis=1) - mrat

    # Stufe 4: Higher-Order Values = ungewichtetes Mittel der zentrierten Basiswerte
    # (kein weiteres MRAT abziehen, jeder Basiswert zählt gleich, z. B. SELFTRANS = (UN + BE) / 2)
    for ho, bvs in higher_order_basic_values(hedonism_to).items():
        out[ho] = out[bvs].mean(axis=1)

    # Stufe 5: Koordinaten
    out["x"] = out["SELFTRANS"] - out["SELFENH"]
    out["y"] = out["OPEN"] - out["CONS"]

    out = out.reset_index()
    return out[[id_col] + SCORE_COLUMNS]


# ---------------------------------------------------------------------------
# Datei-Pipeline + README
# ---------------------------------------------------------------------------

def _readme_text(input_path: Path, output_path: Path, item_map: dict[str, list[str]],
                 id_col: str, hedonism_to: str, n_rows: int,
                 scale_min: int, scale_max: int) -> str:
    rev_const = scale_min + scale_max
    n_items = sum(len(v) for v in item_map.values())
    names = {
        "SD": "Self-Direction / Selbstbestimmung", "ST": "Stimulation / Stimulation",
        "HE": "Hedonism / Hedonismus", "AC": "Achievement / Leistung",
        "PO": "Power / Macht", "SE": "Security / Sicherheit",
        "CO": "Conformity / Konformität", "TR": "Tradition / Tradition",
        "BE": "Benevolence / Wohlwollen", "UN": "Universalism / Universalismus",
        "OPEN": "Openness to Change / Offenheit für Wandel",
        "CONS": "Conservation / Bewahrung",
        "SELFENH": "Self-Enhancement / Selbststärkung",
        "SELFTRANS": "Self-Transcendence / Selbsttranszendenz",
    }
    ho_bv = higher_order_basic_values(hedonism_to)
    ho_items = higher_order_items(item_map, hedonism_to)

    lines = [
        f"# {output_path.name}",
        "",
        f"- **Eingabedatei:** `{input_path.name}`",
        "- **Erzeugt mit:** `ess_pipeline.scoring`",
        f"- **hedonism_to:** `{hedonism_to}`",
        f"- **Zeilen:** {n_rows} (Reihenfolge wie Eingabedatei)",
        "- **Werte:** ungerundet, volle Gleitkomma-Genauigkeit",
        "",
        "## Spalten",
        "",
        "| Spalte | Bedeutung |",
        "|---|---|",
        f"| `{id_col}` | Personen-ID (als String, identisch zur Eingabe) |",
        f"| `MRAT` | Individueller Antwortstil: Mittel aller {n_items} umgepolten Items |",
    ]
    for c in BASIC_VALUES + HIGHER_ORDER:
        lines.append(f"| `{c}` | {names[c]} (MRAT-zentriert) |")
    lines += [
        "| `x` | SELFTRANS − SELFENH (> 0: Fokus auf andere/Gemeinwohl; < 0: eigener Erfolg/Status) |",
        "| `y` | OPEN − CONS (> 0: Wandel/Unabhängigkeit; < 0: Sicherheit/Tradition) |",
        "",
        "## Antwortskala (roh)",
        "",
        "1 = Very much like me, 2 = Like me, 3 = Somewhat like me, 4 = A little like me, "
        "5 = Not like me, 6 = Not like me at all. Keine invertierten Items.",
        "",
        "## Formeln",
        "",
        f"**Stufe 1 – Umpolen:** `x' = {rev_const} − x` für alle {n_items} Items "
        f"(danach {scale_max} = sehr wichtig, {scale_min} = gar nicht wichtig).",
        "",
        f"**Stufe 2 – MRAT:** `MRAT = (Summe aller {n_items} umgepolten Items) / {n_items}`",
        "",
        "**Stufe 3 – Basiswerte:** `Wert = Mittelwert der umgepolten Items − MRAT`",
        "",
        "| Spalte | Formel |",
        "|---|---|",
    ]
    for bv in BASIC_VALUES:
        its = item_map[bv]
        lines.append(f"| `{bv}` | ({' + '.join(i + chr(39) for i in its)}) / {len(its)} − MRAT |")
    lines += [
        "",
        "**Stufe 4 – Higher-Order Values:** ungewichtetes Mittel der (bereits MRAT-zentrierten) "
        "Basiswerte; jeder Basiswert zählt gleich, unabhängig von seiner Item-Zahl.",
        "",
        "| Spalte | Basiswerte | Items | Formel |",
        "|---|---|---|---|",
    ]
    for ho in HIGHER_ORDER:
        bvs = ho_bv[ho]
        its = ho_items[ho]
        lines.append(f"| `{ho}` | {', '.join(bvs)} | {len(its)} ({', '.join(its)}) | "
                     f"({' + '.join(bvs)}) / {len(bvs)} |")
    lines += [
        "",
        "Hinweis: Nach dem Mitteln der zentrierten Basiswerte wird **kein** weiteres MRAT abgezogen "
        "(das wäre eine doppelte Zentrierung).",
        "",
        "Hedonism-Zuordnung (`hedonism_to`): `openness` = HE zählt zu OPEN (Default, Schwartz' "
        "Scoring Key für ESS); `both` = HE zählt zu OPEN und SELFENH; `none` = HE zählt zu keinem "
        "Higher-Order Value.",
        "",
        "**Stufe 5 – Koordinaten:** `x = SELFTRANS − SELFENH`, `y = OPEN − CONS`. "
        "Keine erneute Zentrierung (MRAT kürzt sich heraus).",
        "",
        "## Identitäten (geprüft in `ess_pipeline.validation`)",
        "",
        "- `" + " + ".join(f"{len(item_map[bv])}·{bv}" for bv in BASIC_VALUES) + " = 0` für jede Person",
        f"- `MRAT = {rev_const} − Zeilenmittel der Roh-Items`",
        "",
    ]
    return "\n".join(lines)


def run_scoring(input_csv: str | Path, output_csv: str | Path,
                item_map: dict[str, list[str]] = ESS_ITEM_MAP, id_col: str = ESS_ID_COL,
                hedonism_to: str = "openness", scale_min: int = 1, scale_max: int = 6,
                readme_path: str | Path | None = None) -> pd.DataFrame:
    """Liest die Fragebogen-CSV (ID als String), schreibt Scores-CSV und README. Eingabe bleibt unverändert."""
    input_csv, output_csv = Path(input_csv), Path(output_csv)
    if input_csv.resolve() == output_csv.resolve():
        raise ValueError("Ausgabedatei darf nicht die Eingabedatei sein")
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False, na_values=[])
    scores = compute_scores(df, item_map, id_col, hedonism_to, scale_min, scale_max)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(output_csv, index=False)
    if readme_path is None:
        readme_path = output_csv.with_name(output_csv.stem + "_README.md")
    Path(readme_path).write_text(
        _readme_text(input_csv, output_csv, item_map, id_col, hedonism_to, len(scores), scale_min, scale_max),
        encoding="utf-8",
    )
    return scores

