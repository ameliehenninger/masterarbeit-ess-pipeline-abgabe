"""
Regressionstest: Die Pipeline erzeugt aus den Rohdaten byte-genau (SHA-256) dieselben
Dateien. Läuft nur, wenn die ESS-Rohdaten in data/raw/ liegen.
"""

from __future__ import annotations

import pytest

from ess_pipeline.config import Paths
from ess_pipeline.csv_io import sha256
from ess_pipeline.pipeline import main

EXPECTED = {
    "raw_csv": "4b0bfa73fa86bcf9f868b0a6145f96504a40d7e3f2deeb3e822555993ab32dc8",
    "questionnaire_csv": "597df74dca550aa3924f89992316b0883b9abcdbcc3a8be12e5774bd77db902b",
    "profile_csv": "2afe3d98b215427ef18a518dfa93ccde280d0a57c9ce7a670787dae30b6bd3f2",
    "scores_csv": "ec2bccaf8baf59b3f1d86b192e09a794c86e6e38141ba18d65cee0f8f64cad76",
}

PATHS = Paths()
pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(not (PATHS.raw_csv.exists() and PATHS.codebook_html.exists()),
                       reason="ESS-Rohdaten nicht vorhanden (data/raw/)"),
]


def test_raw_data_is_the_expected_ess_release():
    assert sha256(PATHS.raw_csv) == EXPECTED["raw_csv"]


def test_pipeline_reproduces_previous_results(tmp_path):
    # In einen temporären Projektordner schreiben, damit echte Ergebnisse unberührt bleiben
    (tmp_path / "data" / "raw").mkdir(parents=True)
    for src in (PATHS.raw_csv, PATHS.codebook_html):
        (tmp_path / "data" / "raw" / src.name).symlink_to(src)
    assert main(["--root", str(tmp_path), "--stages", "clean", "score"]) == 0

    tmp = Paths(tmp_path)
    for key in ("questionnaire_csv", "profile_csv", "scores_csv"):
        assert sha256(getattr(tmp, key)) == EXPECTED[key], key
