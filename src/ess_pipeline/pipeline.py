"""
Kommandozeile: führt die komplette Pipeline (Phase 1 + Phase 2) in einem Lauf aus.

    python run_pipeline.py                      # alles: clean -> score -> validate -> plot
    python run_pipeline.py --stages clean       # nur Phase 1
    python run_pipeline.py --stages score validate plot
    python run_pipeline.py --save-intermediate  # zusätzlich Zwischenstand jedes Schritts in data/interim/
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from .cleaning import cleaning_report, run_cleaning
from .config import CleaningConfig, Paths, ScoringConfig
from .csv_io import sha256, write_ess_csv

STAGES = ("clean", "score", "validate", "plot")
log = logging.getLogger("ess_pipeline")


def stage_clean(paths: Paths, cfg: CleaningConfig, save_intermediate: bool) -> None:
    for p in (paths.raw_csv, paths.codebook_html):
        if not p.exists():
            raise FileNotFoundError(f"{p} fehlt – siehe DOKUMENTATION.md, Abschnitt 2.1")
    result = run_cleaning(paths.raw_csv, paths.codebook_html, cfg,
                          interim_dir=paths.interim_dir if save_intermediate else None)
    write_ess_csv(result.questionnaire, paths.questionnaire_csv)
    write_ess_csv(result.profile, paths.profile_csv)
    result.codebook.to_csv(paths.missing_codes_csv, index=False)
    paths.cleaning_report.parent.mkdir(parents=True, exist_ok=True)
    paths.cleaning_report.write_text(cleaning_report(result, paths.raw_csv, sha256(paths.raw_csv)),
                                     encoding="utf-8")
    log.info("Phase 1 fertig: %s, %s", paths.questionnaire_csv.name, paths.profile_csv.name)


def stage_score(paths: Paths, cfg: ScoringConfig) -> None:
    from .scoring import run_scoring

    scores = run_scoring(paths.questionnaire_csv, paths.scores_csv, cfg.item_map, cfg.id_col,
                         cfg.hedonism_to, cfg.scale_min, cfg.scale_max)
    log.info("Scores berechnet: %s (%d Personen)", paths.scores_csv.name, len(scores))


def stage_validate(paths: Paths) -> int:
    from .validation import run_validation

    n_fail = run_validation(paths.profile_csv, paths.questionnaire_csv, paths.scores_csv,
                            paths.validation_report)
    log.info("Validierung: %d fehlgeschlagene Prüfungen", n_fail)
    return n_fail


def stage_plot(paths: Paths) -> None:
    from .plotting import make_figures

    pngs = make_figures(paths.scores_csv, paths.figures_dir)
    log.info("%d Abbildungen in %s", len(pngs), paths.figures_dir)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ESS-11-Pipeline: Bereinigung (Phase 1) und Schwartz-Scores (Phase 2)")
    ap.add_argument("--stages", nargs="+", choices=STAGES, default=list(STAGES),
                    help="auszuführende Stufen (Standard: alle)")
    ap.add_argument("--save-intermediate", action="store_true",
                    help="Zwischenstand jedes Bereinigungsschritts in data/interim/ speichern")
    ap.add_argument("--country", default=CleaningConfig.country, help="Länderfilter (Standard: DE)")
    ap.add_argument("--hedonism-to", default=ScoringConfig.hedonism_to,
                    choices=["openness", "both", "none"], help="Zuordnung von Hedonism (Standard: openness)")
    ap.add_argument("--root", type=Path, default=Paths().root, help="Projektordner")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    paths = Paths(args.root.resolve())
    t0 = time.time()

    if "clean" in args.stages:
        stage_clean(paths, CleaningConfig(country=args.country), args.save_intermediate)
    if "score" in args.stages:
        stage_score(paths, ScoringConfig(hedonism_to=args.hedonism_to))
    n_fail = 0
    if "validate" in args.stages:
        n_fail = stage_validate(paths)
    if "plot" in args.stages:
        stage_plot(paths)

    log.info("Fertig in %.1f s", time.time() - t0)
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
