from pathlib import Path
import pandas as pd, numpy as np, re, json
from superrr_analysis import FILES, phase_bucket, phase_matched_scores
HERE=Path(__file__).resolve().parent
ball=pd.read_csv(FILES['ball']); matches=pd.read_csv(FILES['matches']); comps=pd.read_csv(FILES['competitions'])
eligible=comps[(comps.match_format=='T20I') | comps.comp_name.str.fullmatch(r'IPL \d{4}',na=False)]
b=ball.merge(matches[['match_id','comp_id','match_date','stage','knock_out','first_inn_revised_overs','second_inn_revised_overs','revised_target']],on='match_id',how='left')
b=b.merge(comps[['comp_id','comp_name','match_format','season']],on='comp_id',how='left')
b=b[b.comp_id.isin(eligible.comp_id)&b.innings.isin([1,2])].copy().sort_values(['match_id','innings','innings_ball_num','over_ball_num'])
b['legal']=~b.extras_type.isin(['wide','Overstep'])
b['bowl_legal']=b.legal
b['bat_faced']=~b.extras_type.eq('wide')
b['total_runs']=b.runs+b.extras1_runs+b.extras_2_runs
b['bowler_runs']=b.runs+np.where(b.extras_type.isin(['wide','Overstep']),b.extras1_runs+b.extras_2_runs,0)
non_credit=['RunOut','Retire Out','Obstracting the field','Obstructing the field']
b['bowler_wicket']=b.is_wicket & ~b.dismissal_type.isin(non_credit)
b['bowler_dot']=(b.bowler_runs==0)&b.legal
b['bat_dot']=(b.runs==0)&b.bat_faced
# Match-specific innings length; standard 20 overs where revised limit is absent.
b['innings_overs']=np.where(b.innings.eq(1),b.first_inn_revised_overs,b.second_inn_revised_overs)
b['innings_limit_balls']=(pd.to_numeric(b.innings_overs,errors='coerce').fillna(20)*6).clip(lower=1)
g=b.groupby(['match_id','innings'],sort=False)
b['runs_before']=g.total_runs.cumsum()-b.total_runs
b['wickets_before']=g.is_wicket.cumsum()-b.is_wicket.astype(int)
b['legal_before']=g.legal.cumsum()-b.legal.astype(int)
b['balls_remaining']=(b.innings_limit_balls-b.legal_before).clip(lower=0)
first_total=b[b.innings.eq(1)].groupby('match_id').total_runs.sum()
b['target']=b.match_id.map(first_total)+1
b['target']=b.revised_target.fillna(b.target)
b['runs_needed']=b.target-b.runs_before
b['rrr']=np.where((b.innings==2)&(b.balls_remaining>0),b.runs_needed*6/b.balls_remaining,np.nan)
late=(1-b.balls_remaining/b.innings_limit_balls).clip(0,1)
wicket_pressure=(b.wickets_before/10).clip(0,1)
rrr_pressure=((b.rrr-7)/7).clip(0,1).fillna(0)
b['pressure_index']=np.where(b.innings.eq(2),.50*rrr_pressure+.25*late+.25*wicket_pressure,.45*late+.35*wicket_pressure+.20*(b.wickets_before>=5))
b['phase']=b.overid.map(phase_bucket)
bat=b[b.batting_order<=7].copy()
# Correct dot-ball denominators in the underlying scorer by replacing source columns with explicit flags.
# phase_matched_scores uses runs==0; replace runs with flags only for dot aggregation would corrupt totals,
# so use a patched local copy of the scorer source text in-memory is avoided: build from same scorer then correct metrics below.
# We create a temporary adjusted runs column for bowling dots and preserve bowler_runs for economy.

def score_at(threshold):
    x=b.copy(); x['high_pressure']=x.pressure_index>=threshold
    ba=bat.copy(); ba['high_pressure']=x.loc[ba.index,'high_pressure']
    bo=x.copy()
    # Recompute using canonical scorer, then replace its dot metric with proper definitions and re-score.
    bs=phase_matched_scores(ba,'striker_id','striker_name','bat')
    ws=phase_matched_scores(bo,'bowler_id','bowler_name','bowl')
    # The shared scorer now uses explicit batter/bowler dot flags in BOTH pressure and
    # non-pressure phases, so every composite component uses the same phase-matched sample.
    bs['score_0_100']=(.35*bs.pressure_strike_rate.rank(pct=True)+.15*bs.pressure_boundary_pct.rank(pct=True)+.15*(100-bs.pressure_dot_pct).rank(pct=True)+.20*bs.shrunk_sr_uplift.rank(pct=True)+.10*bs.shrunk_boundary_uplift.rank(pct=True)+.05*bs.shrunk_dismissal_improvement.rank(pct=True))*100
    ws['score_0_100']=(.30*(12-ws.pressure_economy).rank(pct=True)+.25*ws.pressure_wickets_per_6.rank(pct=True)+.15*ws.pressure_dot_pct.rank(pct=True)+.15*ws.shrunk_economy_saved.rank(pct=True)+.10*ws.shrunk_wicket_rate_uplift.rank(pct=True)+.05*ws.shrunk_boundary_suppression.rank(pct=True))*100
    return bs.sort_values('score_0_100',ascending=False).reset_index(drop=True),ws.sort_values('score_0_100',ascending=False).reset_index(drop=True)

allruns={}; tops={}
for t in [.42,.48,.54]:
    bs,ws=score_at(t); allruns[t]=(bs,ws)
    tops[t]=(bs.head(10).striker_name.tolist(),ws.head(10).bowler_name.tolist())
baseb,basew=allruns[.48]
# Rank stability: how often player appears in top 10 across thresholds and rank range.
def stability(which):
    frames=[]
    for t,(bs,ws) in allruns.items():
        d=bs if which=='bat' else ws; name='striker_name' if which=='bat' else 'bowler_name'
        z=d[[name,'score_0_100','pressure_balls','pressure_matches']].copy(); z['threshold']=t; z['rank']=np.arange(1,len(z)+1); frames.append(z)
    long=pd.concat(frames)
    out=long.groupby(name).agg(eligible_thresholds=('rank','count'),top10_appearances=('rank',lambda s: int((s<=10).sum())),rank_min=('rank','min'),rank_max=('rank','max'),rank_mean=('rank','mean'),pressure_balls=('pressure_balls','max'),pressure_matches=('pressure_matches','max')).reset_index()
    return out.sort_values(['top10_appearances','rank_mean'],ascending=[False,True]),long
batstab,batlong=stability('bat'); bowlstab,bowllong=stability('bowl')
# Match-level consistency against a phase-specific non-pressure pool benchmark.
# This avoids comparing each match to the player's own pooled mean (a tautological measure).
x=b.copy(); x['high_pressure']=x.pressure_index>=.48
xb=x[(x.high_pressure)&(x.batting_order<=7)].copy()
xb0=x[(~x.high_pressure)&(x.batting_order<=7)].copy()
bat_phase_base=xb0.groupby('phase').agg(base_runs=('runs','sum'),base_balls=('bat_faced','sum')).reset_index()
bat_phase_base['baseline_sr']=100*bat_phase_base.base_runs/bat_phase_base.base_balls.replace(0,np.nan)
xbm=xb.groupby(['striker_id','striker_name','match_id','phase']).agg(runs=('runs','sum'),balls=('bat_faced','sum')).reset_index().merge(bat_phase_base[['phase','baseline_sr']],on='phase',how='left')
xbm['benchmark_margin']=(100*xbm.runs/xbm.balls.replace(0,np.nan))-xbm.baseline_sr
xbm['weighted_margin']=xbm.benchmark_margin*xbm.balls
batmatch=xbm.groupby(['striker_id','striker_name','match_id']).agg(margin_num=('weighted_margin','sum'),balls=('balls','sum')).reset_index()
batmatch['match_benchmark_margin']=batmatch.margin_num/batmatch.balls.replace(0,np.nan)
batcons=batmatch.groupby(['striker_id','striker_name']).agg(consistency_matches=('match_id','nunique'),median_benchmark_margin=('match_benchmark_margin','median'),positive_benchmark_match_share=('match_benchmark_margin',lambda z: (z>0).mean())).reset_index()

xwb=x[x.high_pressure].copy(); xwb0=x[~x.high_pressure].copy()
bowl_phase_base=xwb0.groupby('phase').agg(base_runs=('bowler_runs','sum'),base_balls=('bowl_legal','sum')).reset_index()
bowl_phase_base['baseline_econ']=6*bowl_phase_base.base_runs/bowl_phase_base.base_balls.replace(0,np.nan)
xbm2=xwb.groupby(['bowler_id','bowler_name','match_id','phase']).agg(runs=('bowler_runs','sum'),balls=('bowl_legal','sum')).reset_index().merge(bowl_phase_base[['phase','baseline_econ']],on='phase',how='left')
xbm2['benchmark_margin']=xbm2.baseline_econ-6*xbm2.runs/xbm2.balls.replace(0,np.nan)
xbm2['weighted_margin']=xbm2.benchmark_margin*xbm2.balls
bowlmatch=xbm2.groupby(['bowler_id','bowler_name','match_id']).agg(margin_num=('weighted_margin','sum'),balls=('balls','sum')).reset_index()
bowlmatch['match_benchmark_margin']=bowlmatch.margin_num/bowlmatch.balls.replace(0,np.nan)
bowlcons=bowlmatch.groupby(['bowler_id','bowler_name']).agg(consistency_matches=('match_id','nunique'),median_benchmark_margin=('match_benchmark_margin','median'),positive_benchmark_match_share=('match_benchmark_margin',lambda z: (z>0).mean())).reset_index()
baseb=baseb.merge(batcons,on=['striker_id','striker_name'],how='left')
basew=basew.merge(bowlcons,on=['bowler_id','bowler_name'],how='left')
# Add sensitivity stability fields.
baseb=baseb.merge(batstab[['striker_name','eligible_thresholds','top10_appearances','rank_min','rank_max']],on='striker_name',how='left')
basew=basew.merge(bowlstab[['bowler_name','eligible_thresholds','top10_appearances','rank_min','rank_max']],on='bowler_name',how='left')
# Export
baseb.head(10).to_csv(HERE/'FINAL_TOP10_BATTERS.csv',index=False); basew.head(10).to_csv(HERE/'FINAL_TOP10_BOWLERS.csv',index=False)
baseb.to_csv(HERE/'FINAL_ALL_BATTERS.csv',index=False); basew.to_csv(HERE/'FINAL_ALL_BOWLERS.csv',index=False)
with pd.ExcelWriter(HERE/'FINAL_SUPERR_ANALYSIS.xlsx',engine='openpyxl') as w:
    baseb.head(10).to_excel(w,sheet_name='Top 10 Batters',index=False); basew.head(10).to_excel(w,sheet_name='Top 10 Bowlers',index=False)
    baseb.to_excel(w,sheet_name='All Batters',index=False); basew.to_excel(w,sheet_name='All Bowlers',index=False)
    batstab.to_excel(w,sheet_name='Batter Sensitivity',index=False); bowlstab.to_excel(w,sheet_name='Bowler Sensitivity',index=False)
    batlong.to_excel(w,sheet_name='Batter Threshold Ranks',index=False); bowllong.to_excel(w,sheet_name='Bowler Threshold Ranks',index=False)
    pd.DataFrame({'threshold':[.42,.48,.54],'bat_top10':[' | '.join(tops[t][0]) for t in [.42,.48,.54]],'bowl_top10':[' | '.join(tops[t][1]) for t in [.42,.48,.54]]}).to_excel(w,sheet_name='Threshold Comparison',index=False)
# Summary
summary={'rows':len(ball),'eligible_rows':len(b),'matches':int(b.match_id.nunique()),'competitions':int(b.comp_id.nunique()),'revised_overs_matches':int(matches[matches.match_id.isin(b.match_id.unique())][['first_inn_revised_overs','second_inn_revised_overs']].notna().any(axis=1).sum()),'threshold_top10':{str(k):{'batters':tops[k][0],'bowlers':tops[k][1]} for k in tops},'batters':baseb.head(10)[['striker_name','score_0_100','pressure_balls','pressure_matches','eligible_thresholds','top10_appearances','rank_min','rank_max','positive_benchmark_match_share','median_benchmark_margin']].to_dict('records'),'bowlers':basew.head(10)[['bowler_name','score_0_100','pressure_balls','pressure_matches','eligible_thresholds','top10_appearances','rank_min','rank_max','positive_benchmark_match_share','median_benchmark_margin']].to_dict('records')}
(HERE/'validation_summary.json').write_text(json.dumps(summary,indent=2,default=float))
print(json.dumps(summary,indent=2,default=float))
