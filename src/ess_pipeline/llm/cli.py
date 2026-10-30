"""
Kommandozeile für Phase 3 (LLM füllt den Fragebogen aus) und Phase 4 (Auswertung):

    python run_llm.py                                  # fill -> score -> analyse -> auswertung
    python run_llm.py --n 10                           # Personenzahl überschreiben
    python run_llm.py --stages score                   # nur Scores aus vorhandener fragebogen_LLM.csv
    python run_llm.py --stages analyse                 # nur Verteilungsanalyse der Wahrscheinlichkeitsvektoren
    python run_llm.py --stages auswertung              # nur Auswertung entlang der Forschungsfragen (Ebene 1 + 2),
                                                       # Abbildungen in <lauf>/figures/
    python run_llm.py --config config/vorexperiment_which_thinking_mode/opus.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from ..config import Paths, ScoringConfig
from .experiment import DETAIL_CSV, QUESTIONNAIRE_CSV, SCORES_CSV, load_config, out_dir, run_fill

STAGES = ("fill", "score", "analyse", "auswertung")
log = logging.getLogger("ess_pipeline.llm")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phase 3: LLM füllt den PVQ-21 in der Rolle von ESS-Personen aus")
    ap.add_argument("--config", type=Path, default=Paths().root / "config" / "llm_experiment.yaml")
    ap.add_argument("--stages", nargs="+", choices=STAGES, default=list(STAGES))
    ap.add_argument("--n", type=int, help="Anzahl Personen (überschreibt persons.n)")
    ap.add_argument("--root", type=Path, default=Paths().root, help="Projektordner")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    paths = Paths(args.root.resolve())
    cfg = load_config(args.config)
    if args.n is not None:
        cfg.persons.n = args.n
    out = out_dir(paths, cfg)
    out.mkdir(parents=True, exist_ok=True)
    # alles, was auf der Konsole erscheint, auch in den Ergebnisordner (angehängt, je Start ein Abschnitt)
    fh = logging.FileHandler(out / "run.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S"))
    logging.getLogger().addHandler(fh)
    log.info("Start: %s, Config %s, Stufen %s", " ".join(sys.argv), args.config, " ".join(args.stages))
    t0 = time.time()

    n_failed = 0
    if "fill" in args.stages:
        results = run_fill(cfg, paths)
        n_failed = sum(not r.ok for r in results)
        if n_failed == len(results):
            log.error("Keine Person erfolgreich – Scores und Auswertung übersprungen, siehe %s",
                      out / "run_report.md")
            return 1
    if "score" in args.stages:
        from ..plotting import make_figures
        from ..scoring import run_scoring

        sc = ScoringConfig()
        scores = run_scoring(out / QUESTIONNAIRE_CSV, out / SCORES_CSV, sc.item_map, sc.id_col,
                             sc.hedonism_to, sc.scale_min, sc.scale_max)
        log.info("Scores berechnet: %s (%d Personen)", out / SCORES_CSV, len(scores))
        pngs = make_figures(out / SCORES_CSV, out / "figures", source_label=f"LLM: {cfg.model.name}")
        log.info("%d Abbildungen in %s", len(pngs), out / "figures")

    if "analyse" in args.stages and (out / DETAIL_CSV).exists() and cfg.prompt.verbalized_sampling:
        from .distributions import REPORT_MD as DIST_MD
        from .distributions import write_report

        m = write_report(out, paths.questionnaire_csv)
        log.info("Verteilungsanalyse: %s (Entropie Mittel %.3f Bit, scharf %.1f %%, flach %.1f %%)",
                 out / DIST_MD, m["entropie_mittel_bit"], 100 * m["anteil_scharf"], 100 * m["anteil_flach"])

    if "auswertung" in args.stages:
        from ..analysis.forschungsfragen import run as run_analysis

        res = run_analysis(out, paths=paths)
        log.info("Auswertung: %s", res / "report.md")

    log.info("Fertig in %.1f s", time.time() - t0)
    return 1 if n_failed else 0


if __name__ == "__main__":
    sys.exit(main())
