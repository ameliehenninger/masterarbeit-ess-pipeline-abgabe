"""Startet Phase 3 (LLM füllt den Fragebogen aus) ohne vorherige Installation: `python run_llm.py --help`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ess_pipeline.llm.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
