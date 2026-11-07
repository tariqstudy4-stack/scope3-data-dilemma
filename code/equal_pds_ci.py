"""Bootstrap 95% intervals for the equal-declared-PDS comparison (Table S2).

Run from the repository root after equal_pds_check.py: python code/equal_pds_ci.py
Bins: realised PDS within +/-5 points of 20, 40, 60 and 80 percent; median error per pattern,
1,000 bootstrap resamples of the pooled runs (seed 1).
"""
import csv, json, collections, os
import numpy as np
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=json.load(open(os.path.join(ROOT,'data','equal_pds_check.json')))
rng=np.random.default_rng(1)
cell=collections.defaultdict(list)
for r in d:
    p=r['pds']*100
    for t in (20,40,60,80):
        if abs(p-t)<=5: cell[(r['indicator'],t,r['pattern'])].append(r['mape'])
rows=[]
for (ind,t,pat),x in sorted(cell.items()):
    x=np.array(x); b=[np.median(rng.choice(x,len(x))) for _ in range(1000)]
    rows.append([ind,t,pat,round(float(np.median(x)),2),round(float(np.percentile(b,2.5)),2),round(float(np.percentile(b,97.5)),2),len(x)])
with open(os.path.join(ROOT,'data','equal_pds_ci.csv'),'w',newline='') as f:
    w=csv.writer(f); w.writerow(['indicator','pds_target','pattern','median_mape','ci_lo','ci_hi','n']); w.writerows(rows)
print(len(rows),'rows written')
