# ESS-Rohdaten beschaffen

Die Rohdaten sind nicht im Repository: Das ESS stellt sie unter CC BY-NC-SA 4.0 bereit und empfiehlt, Datensätze nicht
extern anzubieten, sondern auf das Datenportal zu verweisen.

1. Im ESS-Datenportal anmelden und die Seite der Datei öffnen:
   [ESS11 - integrated file, edition 4.2](https://ess.sikt.no/en/datafile/242aaa39-3bbb-40f5-98bf-bfb1ce53d8ef). Der Download ist kostenlos.
2. Die Datei als CSV herunterladen und als `data/raw/ESS.csv` speichern.
3. Die Variablendokumentation (HTML) herunterladen und als `data/raw/ESS11_Dokumentation.html` speichern.
4. Prüfen, ob es genau die verwendete Version ist:

   ```bash
   shasum -a 256 data/raw/ESS.csv                   # 4b0bfa73fa86bcf9f868b0a6145f96504a40d7e3f2deeb3e822555993ab32dc8
   shasum -a 256 data/raw/ESS11_Dokumentation.html  # 316801aea7f1ae802a92f77c620adc672af24b3bb378711c29aedda5ecbe9ab6
   ```

5. Mit `python run_pipeline.py` die bereinigten Daten in `data/processed/` erzeugen.

Bedingungen laut ESS: nur für nicht kommerzielle Zwecke, Weitergabe abgeleiteter Daten unter denselben Bedingungen,
Quelle korrekt zitieren. Zitation: European Social Survey European Research Infrastructure (ESS ERIC), ESS11 - integrated
file, edition 4.2 [Data set]. DOI: [10.21338/ess11e04_2](https://doi.org/10.21338/ess11e04_2). Das Jahr steht auf der Portalseite der Datei. Abgeleitete Daten werden als
„Adapted from ESS Round 11, edition 4.2“ gekennzeichnet.
