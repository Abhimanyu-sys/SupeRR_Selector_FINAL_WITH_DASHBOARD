SupeRR Selector Season 2 — final validation pack

CONTENTS
- FINAL_METHODOLOGY_REPORT.pdf: updated methodology, shortlist, sensitivity, consistency and limitations
- FINAL_SUPERR_ANALYSIS.xlsx: top tens, full eligible rankings, threshold sensitivity and match-level consistency
- FINAL_TOP10_BATTERS.csv / FINAL_TOP10_BOWLERS.csv: primary threshold 0.48 shortlist
- FINAL_ALL_BATTERS.csv / FINAL_ALL_BOWLERS.csv: full eligible rankings
- validation_summary.json: machine-readable audit and threshold results
- validate_v2.py + superrr_analysis.py: reproducible analysis code
- six supplied CSV files: input dataset
- requirements.txt: Python dependencies

RUN ON MAC
1. Extract this folder.
2. In Terminal, cd into the extracted folder.
3. python3 -m pip install -r requirements.txt
4. python3 validate_v2.py

IMPORTANT METHOD NOTES
- Primary pressure threshold: 0.48; sensitivity thresholds: 0.42 and 0.54.
- Pressure performance is phase-matched against each player's non-pressure performance.
- Dot-ball calculations now use explicit batter and bowler definitions in both pressure and baseline phases.
- Match consistency compares pressure-match performance against phase-specific non-pressure pool benchmarks; it is descriptive, not a significance test.
- The 0.48 rankings are a model shortlist, not definitive auction recommendations. Review sample sizes and threshold stability.
- Dropdown presence confirms selectable names only; it does not establish 2027 auction registration or availability.
- Final selections and interpretation are the participant's responsibility.
