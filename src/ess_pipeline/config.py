"""
Zentrale Konfiguration: Pfade, Item-Mapping und Parameter der Pipeline.

Alle Pfade sind relativ zum Projektordner (Repository-Wurzel). Die Parameter
spiegeln exakt die Entscheidungen aus Phase 1 und Phase 2 wider
(siehe DOKUMENTATION.md, Abschnitte 2 und 3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# ESS 11 – Spalten
# ---------------------------------------------------------------------------

ID_COL = "id"
COUNTRY_COL = "cntry"
IDNO_COL = "idno"

# PVQ-21: Basiswert -> Items (Kreisreihenfolge)
ESS_ITEM_MAP: dict[str, list[str]] = {
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
PVQ_ITEMS: list[str] = [item for items in ESS_ITEM_MAP.values() for item in items]

# Schritt 8: Profilspalten ohne inhaltliche Information über die Person, die aber auf den
# ESS-Datensatz verweisen (mögliche Wiedererkennung durch ein LLM) oder eine andere Spalte
# nur doppelt kodieren. Gewichte und Stichprobendesign (dweight, …, psu) bleiben erhalten.
PROFILE_DROP_GROUPS: dict[str, list[str]] = {
    "Survey-Metadaten": ["name", "essround", "edition", "proddate", "regunit", "mode", "recon"],
    "Interview-Zeitstempel": ["inwds", "ainws", "ainwe", "binwe", "cinwe", "dinwe", "einwe", "finwe",
                              "hinwe", "iinwe", "kinwe", "rinwe", "inwde", "jinws", "jinwe", "inwtm"],
    # nobingnd ist in DE identisch mit gndr; icgndra = Einschätzung der Interviewerin/des Interviewers
    "Geschlecht doppelt": ["nobingnd", "icgndra"],
    # agea bleibt
    "Alter doppelt": ["yrbrn", "agegroup"],
    # ISCED und ES-ISCED sind aus den deutschen Abschlüssen (Schule + Beruf) abgeleitet, die bleiben
    "Bildung doppelt (ISCED, ES-ISCED)": ["edulvlb", "eisced", "edulvlpb", "eiscedp",
                                          "edulvlfb", "eiscedf", "edulvlmb", "eiscedm"],
}
PROFILE_DROP_COLUMNS: list[str] = [c for cols in PROFILE_DROP_GROUPS.values() for c in cols]


# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Paths:
    root: Path = PROJECT_ROOT

    @property
    def raw_csv(self) -> Path:
        return self.root / "data" / "raw" / "ESS.csv"

    @property
    def codebook_html(self) -> Path:
        return self.root / "data" / "raw" / "ESS11_Dokumentation.html"

    @property
    def interim_dir(self) -> Path:
        return self.root / "data" / "interim"

    @property
    def processed_dir(self) -> Path:
        return self.root / "data" / "processed"

    @property
    def questionnaire_csv(self) -> Path:
        return self.processed_dir / "ESS_fragebogen_DE.csv"

    @property
    def profile_csv(self) -> Path:
        return self.processed_dir / "ESS_profil_DE.csv"

    @property
    def missing_codes_csv(self) -> Path:
        return self.processed_dir / "ESS_missing_codes.csv"

    @property
    def results_dir(self) -> Path:
        return self.root / "results"

    @property
    def human_results_dir(self) -> Path:
        return self.results_dir / "mensch"

    @property
    def llm_results_dir(self) -> Path:
        return self.results_dir / "llm"

    @property
    def analysis_dir(self) -> Path:
        """Phase 4: Vergleich Mensch vs. LLM-Twin, je Lauf ein Unterordner."""
        return self.results_dir / "auswertung"

    @property
    def scores_csv(self) -> Path:
        return self.human_results_dir / "ess_scores.csv"

    @property
    def figures_dir(self) -> Path:
        return self.human_results_dir / "figures"

    # Automatisch erzeugte Berichte liegen neben den Daten, die sie beschreiben
    @property
    def cleaning_report(self) -> Path:
        return self.processed_dir / "cleaning_report.md"

    @property
    def validation_report(self) -> Path:
        return self.human_results_dir / "validation_report.txt"


# ---------------------------------------------------------------------------
# Parameter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CleaningConfig:
    country: str = "DE"
    # Schritt 5: Spalten löschen, in denen MEHR als dieser Anteil den Wert "0" hat
    zero_share_threshold: float = 0.5
    items: list[str] = field(default_factory=lambda: list(PVQ_ITEMS))
    # Schritt 8: diese Profilspalten löschen
    drop_profile_columns: list[str] = field(default_factory=lambda: list(PROFILE_DROP_COLUMNS))


@dataclass(frozen=True)
class ScoringConfig:
    item_map: dict[str, list[str]] = field(default_factory=lambda: dict(ESS_ITEM_MAP))
    id_col: str = ID_COL
    hedonism_to: str = "openness"
    scale_min: int = 1
    scale_max: int = 6
