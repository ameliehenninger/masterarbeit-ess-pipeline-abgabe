"""
Phase 1 – Bereinigung des ESS-11-Datensatzes in acht Schritten:

    1. Original-CSV einlesen
    2. Split in Profil (id + alle übrigen Spalten) und Fragebogen (id + 21 PVQ-Items)
    3. Nur Deutschland (cntry == "DE")
    4. Komplett leere Spalten löschen
    5. Spalten löschen, in denen > 50 % der Personen den Wert "0" haben
    6. Missing-Codes laut Codebook (66/77/88/99 usw.) durch leere Zellen ersetzen
    7. Personen mit mindestens einer leeren Fragebogen-Zelle entfernen
    8. Interview-Metadaten, Zeitstempel und doppelte Kodierungen aus dem Profil löschen
       (config.PROFILE_DROP_GROUPS); Gewichte und Stichprobendesign bleiben

Alle Zellen werden als Text behandelt; eine leere Zelle ist "" (nach strip).
Profil und Fragebogen werden immer über die ID abgeglichen, nie über die Position.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .codebook import missing_codes, parse_codebook
from .config import COUNTRY_COL, ID_COL, IDNO_COL, CleaningConfig
from .csv_io import Table, read_ess_csv, write_ess_csv

log = logging.getLogger(__name__)


@dataclass
class StepLog:
    number: int
    title: str
    profile_shape: tuple[int, int]
    questionnaire_shape: tuple[int, int]
    rows_removed: int = 0
    columns_removed: list[str] = field(default_factory=list)
    cells_blanked: int = 0
    note: str = ""


@dataclass
class CleaningResult:
    profile: Table
    questionnaire: Table
    codebook: pd.DataFrame
    steps: list[StepLog]


# ---------------------------------------------------------------------------
# Einzelschritte (reine Funktionen, gut testbar)
# ---------------------------------------------------------------------------

def _is_empty(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(lambda s: s.str.strip() == "")


def split_profile_questionnaire(raw: Table, items: list[str]) -> tuple[Table, Table]:
    """Schritt 2: ID = <cntry>_<idno>; Fragebogen = ID + Items, Profil = ID + Rest."""
    missing = [c for c in [COUNTRY_COL, IDNO_COL] + items if c not in raw.df.columns]
    if missing:
        raise ValueError(f"Spalten fehlen im Rohdatensatz: {missing}")

    df = raw.df
    ids = df[COUNTRY_COL] + "_" + df[IDNO_COL]
    if ids.duplicated().any():
        raise ValueError(f"Doppelte IDs: {ids[ids.duplicated()].unique()[:10].tolist()}")

    item_cols = [c for c in df.columns if c in items]  # Reihenfolge wie im Original
    rest_cols = [c for c in df.columns if c not in items]
    profile = pd.concat([ids.rename(ID_COL), df[rest_cols]], axis=1)
    quest = pd.concat([ids.rename(ID_COL), df[item_cols]], axis=1)
    text = raw.text_columns | {ID_COL}
    return (Table(profile, {c for c in text if c in profile.columns}),
            Table(quest, {c for c in text if c in quest.columns}))


def keep_persons(profile: Table, quest: Table, keep_ids: pd.Series) -> tuple[Table, Table]:
    """Behält nur die IDs aus `keep_ids` (Abgleich per ID, Reihenfolge bleibt erhalten)."""
    keep = set(keep_ids)
    p = profile.subset(rows=profile.df[ID_COL].isin(keep))
    q = quest.subset(rows=quest.df[ID_COL].isin(keep))
    if p.df[ID_COL].tolist() != q.df[ID_COL].tolist():
        raise ValueError("Profil und Fragebogen haben nach dem Filtern unterschiedliche IDs/Reihenfolge")
    return p, q


def complete_questionnaire_ids(quest: Table, items: list[str]) -> pd.Series:
    """Schritt 7: IDs aller Personen ohne leere Item-Zelle."""
    complete = ~_is_empty(quest.df[items]).any(axis=1)
    return quest.df.loc[complete, ID_COL]


def country_ids(profile: Table, country: str) -> pd.Series:
    """Schritt 3: IDs aller Personen aus `country`."""
    return profile.df.loc[profile.df[COUNTRY_COL].str.strip() == country, ID_COL]


def empty_columns(table: Table) -> list[str]:
    """Schritt 4: Spalten, die in allen Zeilen leer sind."""
    return [c for c in table.df.columns if (table.df[c].str.strip() == "").all()]


def mostly_zero_columns(table: Table, threshold: float) -> list[str]:
    """Schritt 5: Spalten, in denen mehr als `threshold` der Zeilen exakt "0" sind."""
    share = table.df.apply(lambda s: (s.str.strip() == "0").mean())
    return share[share > threshold].index.tolist()


def drop_columns(table: Table, columns: list[str], protected: set[str]) -> Table:
    hit = [c for c in columns if c in protected]
    if hit:
        raise ValueError(f"Geschützte Spalten würden gelöscht: {hit}")
    keep = [c for c in table.df.columns if c not in set(columns)]
    return table.subset(columns=keep)


def blank_missing_codes(table: Table, codes: dict[str, set[str]]) -> tuple[Table, int]:
    """Schritt 6: Missing-Codes durch "" ersetzen. Gibt Anzahl ersetzter Zellen zurück."""
    df = table.df.copy()
    n = 0
    for col in df.columns:
        if col in codes:
            hit = df[col].str.strip().isin(codes[col]) & (df[col] != "")
            n += int(hit.sum())
            df[col] = df[col].where(~hit, "")
    return Table(df, table.text_columns), n


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_cleaning(raw_csv: Path, codebook_html: Path, cfg: CleaningConfig | None = None,
                 interim_dir: Path | None = None) -> CleaningResult:
    """Führt die Schritte 1–8 aus. Mit `interim_dir` wird jeder Zwischenstand gespeichert."""
    cfg = cfg or CleaningConfig()
    steps: list[StepLog] = []
    protected = {ID_COL, *cfg.items}

    def record(number: int, title: str, profile: Table | None, quest: Table | None, **kw) -> None:
        shape_p = profile.df.shape if profile is not None else (0, 0)
        shape_q = quest.df.shape if quest is not None else (0, 0)
        step = StepLog(number, title, shape_p, shape_q, **kw)
        steps.append(step)
        log.info("Schritt %d – %s: Profil %s, Fragebogen %s%s", number, title, shape_p, shape_q,
                 f" ({step.note})" if step.note else "")
        if interim_dir is not None and profile is not None:
            out = Path(interim_dir) / f"schritt_{number}"
            write_ess_csv(profile, out / "ESS_profil.csv")
            write_ess_csv(quest, out / "ESS_fragebogen.csv")

    # 1 Einlesen
    raw = read_ess_csv(raw_csv)
    steps.append(StepLog(1, "Original-CSV eingelesen", raw.df.shape, (0, 0)))
    log.info("Schritt 1 – Original-CSV: %s", raw.df.shape)

    # 2 Split
    profile, quest = split_profile_questionnaire(raw, cfg.items)
    del raw
    record(2, "Split in Profil und Fragebogen", profile, quest,
           note="ID = <cntry>_<idno>")

    # 3 Land
    n0 = len(quest.df)
    profile, quest = keep_persons(profile, quest, country_ids(profile, cfg.country))
    record(3, f"Nur {COUNTRY_COL} == {cfg.country}", profile, quest, rows_removed=n0 - len(quest.df))

    # 4 Leere Spalten
    cols_p, cols_q = empty_columns(profile), empty_columns(quest)
    profile = drop_columns(profile, cols_p, protected)
    quest = drop_columns(quest, cols_q, protected)
    record(4, "Komplett leere Spalten gelöscht", profile, quest, columns_removed=cols_p + cols_q)

    # 5 Spalten mit überwiegend 0
    cols_p = mostly_zero_columns(profile, cfg.zero_share_threshold)
    cols_q = mostly_zero_columns(quest, cfg.zero_share_threshold)
    profile = drop_columns(profile, cols_p, protected)
    quest = drop_columns(quest, cols_q, protected)
    record(5, f"Spalten mit > {cfg.zero_share_threshold:.0%} Wert 0 gelöscht", profile, quest,
           columns_removed=cols_p + cols_q)

    # 6 Missing-Codes
    codebook = parse_codebook(codebook_html)
    codes = missing_codes(codebook)
    profile, n_p = blank_missing_codes(profile, codes)
    quest, n_q = blank_missing_codes(quest, codes)
    record(6, "Missing-Codes durch leere Zellen ersetzt", profile, quest, cells_blanked=n_p + n_q,
           note=f"{n_q} Zellen im Fragebogen, {n_p} im Profil")

    # 7 Unvollständige Personen
    n0 = len(quest.df)
    profile, quest = keep_persons(profile, quest, complete_questionnaire_ids(quest, cfg.items))
    record(7, "Personen mit ≥ 1 unbeantworteter Frage entfernt", profile, quest,
           rows_removed=n0 - len(quest.df),
           note="Kriterium: nur die 21 Fragebogen-Items; leere Profil-Zellen bleiben erlaubt")

    # 8 Metadaten und doppelte Kodierungen
    cols_p = [c for c in cfg.drop_profile_columns if c in profile.df.columns]
    absent = [c for c in cfg.drop_profile_columns if c not in profile.df.columns]
    profile = drop_columns(profile, cols_p, protected)
    record(8, "Interview-Metadaten und doppelte Kodierungen gelöscht", profile, quest, columns_removed=cols_p,
           note="Keine inhaltliche Information über die Person, aber Hinweise auf den ESS-Datensatz oder "
                "Doppelkodierungen (siehe config.PROFILE_DROP_GROUPS). Gewichte und Stichprobendesign bleiben."
                + (f" Bereits vorher entfernt: {', '.join(absent)}." if absent else ""))

    return CleaningResult(profile, quest, codebook, steps)


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------

def cleaning_report(result: CleaningResult, raw_csv: Path, raw_sha: str) -> str:
    lines = [
        "# Bereinigungsbericht Phase 1 (automatisch erzeugt)",
        "",
        f"- Eingabe: `{raw_csv.name}` (SHA-256 `{raw_sha[:16]}…`)",
        f"- Ergebnis: {result.questionnaire.df.shape[0]} Personen, "
        f"Profil {result.profile.df.shape[1]} Spalten, Fragebogen {result.questionnaire.df.shape[1]} Spalten",
        "",
        "| Schritt | Beschreibung | Profil (Zeilen × Spalten) | Fragebogen | Zeilen entfernt "
        "| Spalten entfernt | Zellen geleert |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in result.steps:
        q = f"{s.questionnaire_shape[0]} × {s.questionnaire_shape[1]}" if s.questionnaire_shape != (0, 0) else "–"
        lines.append(f"| {s.number} | {s.title} | {s.profile_shape[0]} × {s.profile_shape[1]} | {q} | "
                     f"{s.rows_removed} | {len(s.columns_removed)} | {s.cells_blanked} |")
    lines.append("")
    for s in result.steps:
        if s.note or s.columns_removed:
            lines.append(f"## Schritt {s.number} – {s.title}")
            lines.append("")
            if s.note:
                lines.append(s.note)
                lines.append("")
            if s.columns_removed:
                lines.append(f"Gelöschte Spalten ({len(s.columns_removed)}): "
                             + ", ".join(f"`{c}`" for c in s.columns_removed))
                lines.append("")
    return "\n".join(lines)
