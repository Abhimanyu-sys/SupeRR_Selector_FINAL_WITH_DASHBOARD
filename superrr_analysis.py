#!/usr/bin/env python3
"""
SupeRR Selector Season 2 — reproducible pressure-performance analysis.
Place this script beside the six CSV files and run:
    python superrr_analysis.py
Outputs: superrr_results.xlsx, top10_batters.csv, top10_bowlers.csv,
         eligible_batters.csv, eligible_bowlers.csv, data_audit.txt

Requirements:
    pip install pandas numpy openpyxl
"""
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
FILES = {
    "ball": HERE / "ball_by_ball.csv",
    "mapping": HERE / "competition_team_player_mapping.csv",
    "competitions": HERE / "competitions.csv",
    "matches": HERE / "matches.csv",
    "xi": HERE / "playing_eleven.csv",
    "teams": HERE / "teams.csv",
}

def require_files():
    missing = [str(p.name) for p in FILES.values() if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing CSV files beside script: " + ", ".join(missing))

def phase_bucket(over):
    if over <= 6: return "Powerplay"
    if over <= 15: return "Middle"
    return "Death"

def phase_matched_scores(deliveries, player_id, player_name, mode):
    """Compare pressure and non-pressure performance within the same innings phase."""
    if mode == "bat":
        grp = deliveries.groupby(
            [player_id, player_name, "phase", "high_pressure"], observed=True
        ).agg(
            balls=("bat_faced", "sum"), runs=("runs", "sum"),
            outs=("dismissed_player_id", lambda s: s.notna().sum()),
            fours=("is_four", "sum"), sixes=("is_six", "sum"),
            dots=("bat_dot", "sum"),
            matches=("match_id", "nunique")
        ).reset_index()
    else:
        grp = deliveries.groupby(
            [player_id, player_name, "phase", "high_pressure"], observed=True
        ).agg(
            balls=("bowl_legal", "sum"), conceded=("bowler_runs", "sum"),
            wkts=("bowler_wicket", "sum"), fours=("is_four", "sum"),
            sixes=("is_six", "sum"), dots=("bowler_dot", "sum"),
            matches=("match_id", "nunique")
        ).reset_index()

    p = grp[grp.high_pressure].copy()
    q = grp[~grp.high_pressure].copy()
    m = p.merge(q, on=[player_id, player_name, "phase"], suffixes=("_p", "_b"))
    # Demand usable pressure and ordinary-performance samples in the same phase.
    m = m[(m.balls_p >= 15) & (m.balls_b >= 20)].copy()
    if mode == "bat":
        for s in ["p", "b"]:
            den = m[f"balls_{s}"].replace(0, np.nan)
            m[f"sr_{s}"] = 100 * m[f"runs_{s}"] / den
            m[f"bound_{s}"] = 100 * (m[f"fours_{s}"] + m[f"sixes_{s}"]) / den
            m[f"dot_{s}"] = 100 * m[f"dots_{s}"] / den
            m[f"out_{s}"] = 100 * m[f"outs_{s}"] / den
        m["shrink"] = m.balls_p / (m.balls_p + 50)
        m["sr_delta"] = (m.sr_p - m.sr_b) * m.shrink
        m["bound_delta"] = (m.bound_p - m.bound_b) * m.shrink
        m["dot_delta"] = (m.dot_b - m.dot_p) * m.shrink
        m["out_delta"] = (m.out_b - m.out_p) * m.shrink
        out = m.groupby([player_id, player_name]).apply(lambda x: pd.Series({
            "pressure_balls": x.balls_p.sum(),
            "pressure_matches": x.matches_p.sum(),
            "pressure_strike_rate": np.average(x.sr_p, weights=x.balls_p),
            "phase_matched_baseline_sr": np.average(x.sr_b, weights=x.balls_p),
            "pressure_boundary_pct": np.average(x.bound_p, weights=x.balls_p),
            "pressure_dot_pct": np.average(x.dot_p, weights=x.balls_p),
            "shrunk_sr_uplift": np.average(x.sr_delta, weights=x.balls_p),
            "shrunk_boundary_uplift": np.average(x.bound_delta, weights=x.balls_p),
            "shrunk_dot_improvement": np.average(x.dot_delta, weights=x.balls_p),
            "shrunk_dismissal_improvement": np.average(x.out_delta, weights=x.balls_p),
            "phase_coverage": x.phase.nunique()
        }), include_groups=False).reset_index()
        exact_matches = deliveries[deliveries.high_pressure].groupby(player_id).match_id.nunique()
        out["pressure_matches"] = out[player_id].map(exact_matches).fillna(0)
        out = out[(out.pressure_balls >= 60) & (out.pressure_matches >= 8) & (out.phase_coverage >= 2)].copy()
        # Percentile composite: execution under pressure plus improvement over like-for-like phase baseline.
        out["score_0_100"] = (
            .35*out.pressure_strike_rate.rank(pct=True)
            + .15*out.pressure_boundary_pct.rank(pct=True)
            + .15*(100-out.pressure_dot_pct).rank(pct=True)
            + .20*out.shrunk_sr_uplift.rank(pct=True)
            + .10*out.shrunk_boundary_uplift.rank(pct=True)
            + .05*out.shrunk_dismissal_improvement.rank(pct=True)
        ) * 100
    else:
        for s in ["p", "b"]:
            den = m[f"balls_{s}"].replace(0, np.nan)
            m[f"econ_{s}"] = 6 * m[f"conceded_{s}"] / den
            m[f"wkt6_{s}"] = 6 * m[f"wkts_{s}"] / den
            m[f"dot_{s}"] = 100 * m[f"dots_{s}"] / den
            m[f"bound6_{s}"] = 6 * (m[f"fours_{s}"] + m[f"sixes_{s}"]) / den
        m["shrink"] = m.balls_p / (m.balls_p + 50)
        m["econ_saved"] = (m.econ_b - m.econ_p) * m.shrink
        m["wicket_rate_uplift"] = (m.wkt6_p - m.wkt6_b) * m.shrink
        m["dot_uplift"] = (m.dot_p - m.dot_b) * m.shrink
        m["boundary_suppression"] = (m.bound6_b - m.bound6_p) * m.shrink
        out = m.groupby([player_id, player_name]).apply(lambda x: pd.Series({
            "pressure_balls": x.balls_p.sum(),
            "pressure_matches": x.matches_p.sum(),
            "pressure_economy": np.average(x.econ_p, weights=x.balls_p),
            "phase_matched_baseline_economy": np.average(x.econ_b, weights=x.balls_p),
            "pressure_wickets_per_6": np.average(x.wkt6_p, weights=x.balls_p),
            "pressure_dot_pct": np.average(x.dot_p, weights=x.balls_p),
            "shrunk_economy_saved": np.average(x.econ_saved, weights=x.balls_p),
            "shrunk_wicket_rate_uplift": np.average(x.wicket_rate_uplift, weights=x.balls_p),
            "shrunk_dot_uplift": np.average(x.dot_uplift, weights=x.balls_p),
            "shrunk_boundary_suppression": np.average(x.boundary_suppression, weights=x.balls_p),
            "phase_coverage": x.phase.nunique()
        }), include_groups=False).reset_index()
        exact_matches = deliveries[deliveries.high_pressure].groupby(player_id).match_id.nunique()
        out["pressure_matches"] = out[player_id].map(exact_matches).fillna(0)
        out = out[(out.pressure_balls >= 60) & (out.pressure_matches >= 8) & (out.phase_coverage >= 2)].copy()
        out["score_0_100"] = (
            .30*(12-out.pressure_economy).rank(pct=True)
            + .25*out.pressure_wickets_per_6.rank(pct=True)
            + .15*out.pressure_dot_pct.rank(pct=True)
            + .15*out.shrunk_economy_saved.rank(pct=True)
            + .10*out.shrunk_wicket_rate_uplift.rank(pct=True)
            + .05*out.shrunk_boundary_suppression.rank(pct=True)
        ) * 100
    return out.sort_values("score_0_100", ascending=False).reset_index(drop=True)

def main():
    require_files()
    ball = pd.read_csv(FILES["ball"])
    matches = pd.read_csv(FILES["matches"])
    comps = pd.read_csv(FILES["competitions"])
    # Keep the challenge's IPL + T20I scope; exclude unrelated domestic T20 competitions.
    ipl = comps.comp_name.str.fullmatch(r"IPL \d{4}", na=False)
    eligible_comps = comps[(comps.match_format == "T20I") | ipl]
    b = ball.merge(matches[["match_id","comp_id","match_date","stage","knock_out",
                            "first_inn_revised_overs","second_inn_revised_overs",
                            "revised_target"]], on="match_id", how="left")
    b = b.merge(comps[["comp_id","comp_name","match_format","season"]], on="comp_id", how="left")
    b = b[b.comp_id.isin(eligible_comps.comp_id) & b.innings.isin([1,2])].copy()
    b = b.sort_values(["match_id","innings","innings_ball_num","over_ball_num"])
    b["legal"] = ~b.extras_type.isin(["wide","Overstep"])
    b["bowl_legal"] = b["legal"]
    b["bat_faced"] = ~b.extras_type.eq("wide")
    b["total_runs"] = b.runs + b.extras1_runs + b.extras_2_runs
    b["bowler_runs"] = b.runs + np.where(
        b.extras_type.isin(["wide","Overstep"]), b.extras1_runs+b.extras_2_runs, 0
    )
    non_credit = ["RunOut","Retire Out","Obstracting the field","Obstructing the field"]
    b["bowler_wicket"] = b.is_wicket & ~b.dismissal_type.isin(non_credit)
    g = b.groupby(["match_id","innings"], sort=False)
    b["runs_before"] = g.total_runs.cumsum() - b.total_runs
    b["wickets_before"] = g.is_wicket.cumsum() - b.is_wicket.astype(int)
    b["legal_before"] = g.legal.cumsum() - b.legal.astype(int)
    # Standard 20-over context; revised-overs fields are retained for audit and limitations.
    b["balls_remaining"] = (120 - b.legal_before).clip(lower=0)
    first_total = b[b.innings == 1].groupby("match_id").total_runs.sum()
    b["target"] = b.match_id.map(first_total) + 1
    # Use published revised target where present.
    b["target"] = b.revised_target.fillna(b.target)
    b["runs_needed"] = b.target - b.runs_before
    b["rrr"] = np.where((b.innings == 2) & (b.balls_remaining > 0),
                        b.runs_needed*6/b.balls_remaining, np.nan)
    late = (1 - b.balls_remaining/120).clip(0,1)
    wicket_pressure = (b.wickets_before/10).clip(0,1)
    rrr_pressure = ((b.rrr-7)/7).clip(0,1).fillna(0)
    first_idx = .45*late + .35*wicket_pressure + .20*(b.wickets_before >= 5)
    second_idx = .50*rrr_pressure + .25*late + .25*wicket_pressure
    b["pressure_index"] = np.where(b.innings == 2, second_idx, first_idx)
    b["high_pressure"] = b.pressure_index >= .48
    b["phase"] = b.overid.map(phase_bucket)
    # Batters: top-seven batting positions only, so tail-end bowlers do not dominate a batting list.
    bat = b[b.batting_order <= 7].copy()
    bat_scores = phase_matched_scores(bat, "striker_id", "striker_name", "bat")
    bowl_scores = phase_matched_scores(b, "bowler_id", "bowler_name", "bowl")
    # Data audit
    audit = [
        f"Ball-by-ball rows in supplied file: {len(ball):,}",
        f"Eligible deliveries after IPL + T20I filter and innings 1-2: {len(b):,}",
        f"Eligible matches represented in ball data: {b.match_id.nunique():,}",
        f"Eligible competitions: {b.comp_id.nunique():,}",
        f"Date range: {b.match_date.min()} to {b.match_date.max()}",
        f"High-pressure delivery share: {b.high_pressure.mean():.1%}",
        f"Matches with at least one high-pressure delivery: {b.loc[b.high_pressure,'match_id'].nunique():,}",
        f"Eligible batters after sample/phase filters: {len(bat_scores):,}",
        f"Eligible bowlers after sample/phase filters: {len(bowl_scores):,}",
        "Pressure thresholds: composite pressure index >= 0.48.",
        "Batters: top-seven batting positions; >=60 pressure balls, >=8 pressure matches, >=2 phases; >=15 pressure and >=20 baseline balls within each matched phase.",
        "Bowlers: >=60 pressure legal balls, >=8 pressure matches, >=2 phases; >=15 pressure and >=20 baseline balls within each matched phase.",
        "Baseline comparisons are phase-matched (powerplay 1-6, middle 7-15, death 16-20).",
        "Scores are relative percentile composites within eligible player pools, not probabilities or absolute talent ratings.",
        "Limitations: standard 120-ball context; shortened/DLS innings and super overs require manual review; player availability/auction eligibility is not inferred."
    ]
    (HERE/"data_audit.txt").write_text("\n".join(audit), encoding="utf-8")
    bat_scores.head(10).to_csv(HERE/"top10_batters.csv", index=False)
    bowl_scores.head(10).to_csv(HERE/"top10_bowlers.csv", index=False)
    bat_scores.to_csv(HERE/"eligible_batters.csv", index=False)
    bowl_scores.to_csv(HERE/"eligible_bowlers.csv", index=False)
    with pd.ExcelWriter(HERE/"superrr_results.xlsx", engine="openpyxl") as writer:
        bat_scores.head(10).to_excel(writer, sheet_name="Top 10 Batters", index=False)
        bowl_scores.head(10).to_excel(writer, sheet_name="Top 10 Bowlers", index=False)
        bat_scores.to_excel(writer, sheet_name="All Eligible Batters", index=False)
        bowl_scores.to_excel(writer, sheet_name="All Eligible Bowlers", index=False)
        pd.DataFrame({"Audit":audit}).to_excel(writer, sheet_name="Method & Audit", index=False)
    print("\nTOP 10 BATTERS")
    print(bat_scores.head(10)[["striker_name","score_0_100","pressure_balls","pressure_matches"]].to_string(index=False))
    print("\nTOP 10 BOWLERS")
    print(bowl_scores.head(10)[["bowler_name","score_0_100","pressure_balls","pressure_matches"]].to_string(index=False))
    print("\nCreated superrr_results.xlsx, CSV rankings, and data_audit.txt")

if __name__ == "__main__":
    main()
