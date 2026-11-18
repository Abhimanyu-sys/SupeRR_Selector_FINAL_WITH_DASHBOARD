SupeRR Selector Season 2 — FINAL PACKAGE WITH DASHBOARD

CONTENTS
- FINAL_METHODOLOGY_REPORT.pdf: final methodology and limitations
- FINAL_SUPERR_ANALYSIS.xlsx: analysis workbook
- FINAL_TOP10_BATTERS.csv / FINAL_TOP10_BOWLERS.csv: primary 0.48 shortlist
- FINAL_ALL_BATTERS.csv / FINAL_ALL_BOWLERS.csv: full eligible rankings
- validation_summary.json: validation output
- validate_v2.py + superrr_analysis.py: reproducible analysis code
- six supplied CSVs: source data pack (keep private; do not publish)
- dashboard/index.html: standalone interactive dashboard with embedded aggregate results

RUN ANALYSIS ON MAC
1. Extract the ZIP.
2. Open Terminal and cd into the extracted SupeRR_Selector_FINAL_WITH_DASHBOARD folder.
3. Install dependencies: python3 -m pip install -r requirements.txt
4. Run validation: python3 validate_v2.py

In short Final running commands on mac 
1. Terminal-1: python3 -m http.server 8000
2. Terminal-2: open http://localhost:8000/dashboard/index.html

PREVIEW DASHBOARD ON MAC
From the project root, run: python3 -m http.server 8000
Then open: http://localhost:8000/dashboard/
Stop the local server with Control+C in Terminal.

IMPORTANT
- Primary pressure threshold: 0.48; sensitivity thresholds: 0.42 and 0.54.
- The dashboard is self-contained and embeds aggregate player-level results; it does not fetch data from the CSVs.
- The analysis script regenerates the final CSV, XLSX, JSON and PDF outputs. The dashboard is a static snapshot of the V3 results bundled here. If you rerun analysis and results change, refresh the dashboard data before publishing.
- Do not publish the original ball_by_ball.csv or other supplied challenge data. Check competition rules before publishing even derived results.
- Dropdown presence does not establish player registration, retention, release or 2027 auction availability.
- Rankings are decision-support analysis, not guarantees of future performance or official Rajasthan Royals recommendations.
