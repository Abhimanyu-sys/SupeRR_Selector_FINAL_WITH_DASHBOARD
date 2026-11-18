# SupeRR Selector — IPL 2027 Auction Analytics

**A data-driven cricket analytics project exploring player performance under pressure to support Rajasthan Royals' IPL 2027 auction strategy.**

## Project Overview

SupeRR Selector evaluates batting and bowling performances under pressure using IPL and T20I ball-by-ball data.

The objective is to identify players who demonstrate reliable performance in challenging match situations and provide an analytical foundation for auction shortlisting.

## Key Features

- **Pressure-based performance analysis:** Evaluates player contributions in high-pressure situations.
- **Top 10 batter rankings:** Identifies high-performing batters under pressure.
- **Top 10 bowler rankings:** Identifies bowlers with reliable pressure performance.
- **Composite scoring:** Combines multiple performance indicators into comparative scores.
- **Sample-size analysis:** Considers pressure balls and matches to provide context to rankings.
- **Sensitivity analysis:** Tests ranking changes across multiple pressure thresholds.
- **Interactive dashboard:** Presents rankings, comparisons, and methodology in an accessible interface.

## Technology Stack

- Python
- Pandas
- NumPy
- HTML
- CSS
- JavaScript
- Excel

## Project Structure

```text
SupeRR_Selector_FINAL_WITH_DASHBOARD/
│
├── index.html
├── superrr_analysis.py
├── validate_v2.py
├── requirements.txt
├── validation_summary.json
│
├── FINAL_ALL_BATTERS.csv
├── FINAL_ALL_BOWLERS.csv
├── FINAL_TOP10_BATTERS.csv
├── FINAL_TOP10_BOWLERS.csv
│
└── FINAL_SUPERR_ANALYSIS.xlsx
```

## Running the Dashboard Locally

Clone the repository:

```bash
git clone https://github.com/Abhimanyu-sys/SupeRR_Selector_FINAL_WITH_DASHBOARD.git
```

Navigate into the project:

```bash
cd SupeRR_Selector_FINAL_WITH_DASHBOARD
```

Start a local server:

```bash
python3 -m http.server 8000
```

Open:

```text
http://localhost:8000/
```

## Methodology

The analysis uses ball-by-ball performance data to identify pressure situations and compare player performance through a composite scoring framework.

Multiple pressure thresholds are evaluated to understand ranking stability. Player sample sizes and match-level consistency are also considered.

## Important Limitations

- Historical performance does not guarantee future performance.
- Player rankings depend on the selected pressure definition and scoring methodology.
- Sample sizes differ between players.
- Rankings do not independently establish player availability or eligibility for the IPL 2027 auction.

## Disclaimer

This project is an independent analytical submission for the SupeRR Selector Season 2 challenge. It is not an official Rajasthan Royals recommendation or endorsement.

**Author:** Abhimanyu Rajput  
**GitHub:** [Abhimanyu-sys](https://github.com/Abhimanyu-sys)
