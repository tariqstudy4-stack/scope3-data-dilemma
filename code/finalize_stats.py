import json
import numpy as np
from collections import defaultdict

rows = []
for i in range(4):
    rows.extend(json.load(open(f"data/results_400_{i}.json")))
print("total rows:", len(rows))

def agg(rows, **filt):
    out = [r for r in rows if all(r[k] == v for k, v in filt.items())]
    return out

indicators = sorted(set(r["indicator"] for r in rows))
patterns = sorted(set(r["pattern"] for r in rows))
rates = sorted(set(r["rate"] for r in rows))
print("indicators:", indicators)
print("patterns:", patterns)
print("rates:", rates)

# tiers encoding: 0 == converged (None), else 1,2,3
def mape_at(indicator, pattern, rate, tiers):
    rs = agg(rows, indicator=indicator, pattern=pattern, rate=rate, tiers=tiers)
    return float(np.median([r["mape"] for r in rs]))

print("\n=== FLOORS (rate=0, converged) ===")
floors = {}
for ind in indicators:
    v = mape_at(ind, patterns[0], 0.0, 0)
    floors[ind] = v
    print(ind, round(v, 2))

print("\n=== HALVING THRESHOLDS per pattern/indicator (converged) ===")
halve = defaultdict(dict)
for ind in indicators:
    floor = floors[ind]
    target = floor / 2
    for pat in patterns:
        thr = None
        for rate in rates:
            v = mape_at(ind, pat, rate, 0)
            if v <= target:
                thr = rate
                break
        halve[ind][pat] = thr
        print(ind, pat, "halving at rate=", thr, " (target<=", round(target,2), ")")

print("\n=== flow vs random/cluster: does flow reach halving no later, strictly earlier for how many? ===")
count_strict = 0
for ind in indicators:
    f = halve[ind].get("flow")
    others = [halve[ind].get(p) for p in patterns if p != "flow" and p != "strategic"]
    others = [o for o in others if o is not None]
    if f is not None and others:
        no_later = all(f <= o for o in others)
        strictly_earlier = any(f < o for o in others)
        print(ind, "flow=", f, "others=", others, "no_later_than_all=", no_later, "strictly_earlier_than_some=", strictly_earlier)
        if strictly_earlier:
            count_strict += 1
print("indicators where flow strictly earlier than at least one alt:", count_strict, "/", len(indicators))

print("\n=== Chaining depth interaction (GHG, flow, T=1 vs converged) at 20% and 80% ===")
for rate in [0.20, 0.80]:
    for tiers in [1, 0]:
        v = mape_at("GHG", "flow", rate, tiers)
        print(f"rate={rate} tiers({'T=1' if tiers==1 else 'converged'})={round(v,2)}")

print("\n=== T=1 non-monotonicity (GHG flow) across rates ===")
for rate in rates:
    v = mape_at("GHG", "flow", rate, 1)
    print(rate, round(v, 3))

print("\n=== Coverage (flow pattern) at rate=0 and rate=0.8, converged ===")
def cov_at(indicator, pattern, rate, tiers):
    rs = agg(rows, indicator=indicator, pattern=pattern, rate=rate, tiers=tiers)
    return float(np.mean([r["coverage"] for r in rs])), float(np.mean([r["rel_width"] for r in rs]))
for ind in indicators:
    c0, w0 = cov_at(ind, "flow", 0.0, 0)
    c8, w8 = cov_at(ind, "flow", 0.8, 0)
    print(ind, "coverage@0%=", round(c0,1), "width@0%=", round(w0,2), " | coverage@80%=", round(c8,1), "width@80%=", round(w8,2))

print("\n=== Ranking flips pooled (converged, database-only vs participation) ===")
for rate in rates:
    fs = []
    for ind in indicators:
        rs = agg(rows, indicator=ind, pattern="flow", rate=rate, tiers=0)
        fs.extend([r["flips"] for r in rs if not np.isnan(r["flips"])])
    print("rate=", rate, "pooled median flips % =", round(float(np.median(fs)),2))

print("\n=== Self-selection (strategic) headline: does error rise with participation for how many indicators? ===")
for ind in indicators:
    v0 = mape_at(ind, "strategic", 0.0, 0)
    v100 = mape_at(ind, "strategic", 1.0, 0)
    direction = "WORSE (rises)" if v100 > v0 else "better (falls)"
    print(ind, "err@0%=", round(v0,2), "err@100%=", round(v100,2), direction)

print("\n=== Table 1 data: pattern x indicator: floor, halving rate, coverage@80, p90@80, max@80 (converged) ===")
def p90_at(indicator, pattern, rate, tiers):
    rs = agg(rows, indicator=indicator, pattern=pattern, rate=rate, tiers=tiers)
    return float(np.mean([r["p90"] for r in rs])), float(np.mean([r["maxape"] for r in rs]))

for pat in ["random", "flow", "cluster", "strategic"]:
    for ind in indicators:
        floor = mape_at(ind, pat, 0.0, 0)
        thr = halve[ind][pat]
        cov80, w80 = cov_at(ind, pat, 0.8, 0)
        p9080, max80 = p90_at(ind, pat, 0.8, 0)
        print(f"{pat:10s} {ind:6s} floor={floor:6.2f} halve_at={thr} cov80={cov80:5.1f} p90_80={p9080:6.1f} max80={max80:7.1f}")
