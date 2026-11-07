"""Independent end-to-end verification of the PCF cascade benchmark."""
import json, urllib.request
import numpy as np
from cascade import (cascade_reports, target_pcf, true_pcf,
                     secondary_factors, mape, ranking_flips)
from patterns import sample
from experiments import cascade_batch, primary_data_share, RATES, TIERS, GSD, N_DRAWS

d = np.load("data/matrices.npz", allow_pickle=True)
A, E, Z, x, F = d["A"], d["E"], d["Z"], d["x"], d["F"]
inds = list(d["industries"]); n = len(inds)
manuf = list(d["manuf"]); tidx = np.array([inds.index(c) for c in manuf])
sections = np.array([c[0] for c in inds]); supply = Z.sum(axis=1) + 1e-9
M = true_pcf(A, E); S = secondary_factors(M, inds)
ok = lambda name, cond, detail="": print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")

# ---- 1. DATA: spot-check stored cells against the live Eurostat API -------
def api(url):
    return json.load(urllib.request.urlopen(url, timeout=90))

base = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
spots = [("C20", "C24"), ("C29", "C28"), ("D", "C23")]
rel = []
for r_, c_ in spots:
    u = f"{base}/naio_10_cp1750?format=JSON&lang=EN&time=2022&geo=EU27_2020&unit=MIO_EUR&stk_flow=TOTAL&ind_ava={r_}&ind_use={c_}"
    try:
        v = list(api(u)["value"].values())
    except Exception as exc:
        print(f"[INFO] 1a live API not reachable ({exc.__class__.__name__}); stored matrices are used"); rel = None; break
    live = float(v[0]) if v else 0.0
    stored = Z[inds.index(r_), inds.index(c_)]
    rel.append(abs(live - stored) / stored)
if rel:
    # Eurostat revises published tables; the stored matrices are the vintage behind the manuscript and are not rebuilt
    print(f"[INFO] 1a SIOT spot cells vs live API: max relative difference {max(rel):.1%} "
          "(informational; the stored data/matrices.npz is the vintage used in the paper)")
u = f"{base}/env_ac_ainah_r2?format=JSON&lang=EN&time=2022&geo=EU27_2020&unit=THS_T&airpol=GHG&nace_r2=C24"
live = float(list(api(u)["value"].values())[0])
ok("1b emissions spot cell (C24 GHG)", abs(live - F[0, inds.index("C24")]) < 0.5,
   f"live={live:.0f} stored={F[0, inds.index('C24')]:.0f}")
ok("1c GHG total vs Eurostat", abs(json.load(open('data/checks.json'))["ghg_mapped_vs_published_pct"]) < 0.2)
ok("1d technosphere economics: all column sums < 1",
   bool((A.sum(axis=0) < 1).all()), f"max={A.sum(axis=0).max():.3f}")
ok("1e spectral radius < 1", np.max(np.abs(np.linalg.eigvals(A))) < 1)

# ---- 2. GROUND TRUTH: Leontief identity + series convergence ---------------
ok("2a M(I-A) == E (Leontief identity)",
   np.allclose(M @ (np.eye(n) - A), E, atol=1e-12))
Mser = E.copy(); term = E.copy()
for _ in range(300):
    term = term @ A
    Mser += term
ok("2b power-series Leontief agrees with inverse",
   np.allclose(Mser, M, rtol=1e-10))

# ---- 3. SECONDARY FACTORS: leave-one-out property ---------------------------
j = inds.index("C24")
M2 = M.copy(); M2[:, j] *= 10          # perturb target's own truth
S2 = secondary_factors(M2, inds)
ok("3a S[:,j] independent of industry j's own value",
   np.allclose(S2[:, j], S[:, j]))
sing = [i for i in range(n) if (sections == sections[i]).sum() == 1]
from cascade import _SUPERSECTION, _SUPERSECTION_MEMBERS
def _sup_mean(i):
    mem = _SUPERSECTION_MEMBERS[_SUPERSECTION[sections[i]]]
    return M[:, [k for k in range(n) if sections[k] in mem and k != i]].mean(axis=1)
ok("3b singleton sections get the leave-one-out mean of their Eurostat supersection",
   all(np.allclose(S[:, i], _sup_mean(i)) for i in sing),
   f"(n singletons={len(sing)})")

# ---- 4. SOLVER: independent linear-solve implementation --------------------
rng = np.random.default_rng(123)
P = sample("random", n, 0.5, rng)
k = 1; e, s_row = E[k], S[k]
# fixed point solved directly as a linear system:
# r = P*(e + A^T r) + (1-P)*s  ->  (I - diag(P) A^T) r = P*e + (1-P)*s
Pm = np.diag(P.astype(float))
r_lin = np.linalg.solve(np.eye(n) - Pm @ A.T, P * e + (~P) * s_row)
r_fix = cascade_reports(A, e, s_row, P, None)
ok("4a fixed-point == direct linear solve", np.allclose(r_lin, r_fix, atol=1e-9))
ok("4b batch impl == scalar impl",
   np.allclose(cascade_batch(A, e, s_row[None, :], P, None)[0],
               target_pcf(A, e, r_fix), atol=1e-9))
ok("4c full participation reproduces truth",
   np.allclose(target_pcf(A, e, cascade_reports(A, e, s_row,
                np.ones(n, bool), None)), M[k], rtol=1e-8))
ok("4d zero participation == analytic PACT floor",
   np.allclose(target_pcf(A, e, cascade_reports(A, e, s_row,
                np.zeros(n, bool), None)), e + s_row @ A))
t_err = [np.max(np.abs(target_pcf(A, e, cascade_reports(A, e, s_row, P, t))
                       - target_pcf(A, e, r_fix))) for t in (1, 3, 10, 50)]
ok("4e tier iteration converges to fixed point monotonically",
   all(t_err[i] >= t_err[i+1] - 1e-12 for i in range(3)) and t_err[-1] < 1e-8,
   f"errs={['%.1e' % v for v in t_err]}")

# ---- 5. PDS: analytic identities -------------------------------------------
pds0 = primary_data_share(A, e, s_row, np.zeros(n, bool), None)
valid = (e + s_row @ A) > 1e-30
ok("5a PDS at zero participation == own-gate share e/(e+sA)",
   np.allclose(pds0[valid], (e / np.maximum(e + s_row @ A, 1e-30))[valid])
   and np.allclose(pds0[~valid], 0.0))
pds1 = primary_data_share(A, e, s_row, np.ones(n, bool), None)
ok("5b PDS at full participation == 1 (non-degenerate industries)",
   np.allclose(pds1[valid], 1.0) and np.allclose(pds1[~valid], 0.0))
pds_mid = primary_data_share(A, e, s_row, P, None)
ok("5c PDS in (0,1] at partial participation (non-degenerate)",
   bool((pds_mid[valid] > 0).all() and (pds_mid[valid] <= 1 + 1e-12).all()))

# ---- 6. PATTERNS -------------------------------------------------------------
c1 = all(sample("random", n, r, np.random.default_rng(s)).sum()
         == int(round(r * n)) for r in RATES for s in range(3))
ok("6a all patterns hit requested count (random)", c1)
fs = [supply[sample("flow", n, 0.2, np.random.default_rng(s), supply=supply,
      sections=sections)].sum() / supply.sum() for s in range(20)]
rs = [supply[sample("random", n, 0.2, np.random.default_rng(s), supply=supply,
      sections=sections)].sum() / supply.sum() for s in range(20)]
ok("6b flow pattern captures more supply than random at same count",
   np.mean(fs) > np.mean(rs), f"flow={np.mean(fs):.2f} rand={np.mean(rs):.2f}")
pc = sample("cluster", n, 0.4, np.random.default_rng(7), sections=sections)
touched = {sec: (pc[sections == sec].mean()) for sec in np.unique(sections)}
ok("6c cluster pattern = whole sections (plus one trimmed)",
   sum(0 < v < 1 for v in touched.values()) <= 1)

# ---- 7. METRICS on analytic toy ---------------------------------------------
truth = np.array([1.0, 2.0, 3.0, 4.0]); est = np.array([1.1, 1.9, 3.3, 3.6])
ok("7a MAPE correct", abs(mape(est, truth, np.arange(4)) - 10.0) < 1e-9)
est2 = np.array([2.0, 1.0, 3.0, 4.0])   # one reversal among 6 material pairs
fl, npairs = ranking_flips(est2, truth, np.arange(4))
ok("7b ranking flips correct", abs(fl - 100 / 6) < 1e-9 and npairs == 6)

# ---- 8. REPRODUCE random grid cells from scratch ----------------------------
rows = json.load(open("data/results.json"))
rng2 = np.random.default_rng(99)
sigma = np.log(GSD); good = True
for idx in rng2.choice(len(rows), 5, replace=False):
    r = rows[idx]
    k = list(d["airpol"]).index(r["indicator"])
    tiers = None if r["tiers"] == 0 else r["tiers"]
    import hashlib
    key = f"{k}|{r['pattern']}|{r['rate']}|{tiers}|{r['seed']}"
    rr = np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8], 16))
    P = sample(r["pattern"], n, r["rate"], rr, supply=supply, sections=sections)
    pt = cascade_batch(A, E[k], S[k][None, :], P, tiers)[0]
    good &= abs(mape(pt, M[k], tidx) - r["mape"]) < 1e-9
ok("8a 5 random grid cells reproduce exactly from scratch", good)

# ---- 9. INTERVAL MACHINERY ---------------------------------------------------
# 9a: the mean-preserving draws obtained by the affine shortcut equal a direct computation with rescaled secondary draws.
# 9b: when the substitute error is random and unbiased (mean-1 lognormal, GSD 2.0) and the widening is mean-preserving,
#     the 95% interval covers close to nominal (the full factorial control is code/calibration_control.py).
from intervals import mean_preserving, coverage_width
rr = np.random.default_rng(7)
Pq = sample("flow", n, 0.6, rr, supply=supply, sections=sections)
noise = rr.lognormal(0.0, sigma, size=(50, n)); Sd = S[1][None, :] * noise
d_aff = mean_preserving(cascade_batch(A, E[1], Sd, Pq, None), cascade_batch(A, E[1], np.zeros((1, n)), Pq, None), sigma)
d_dir = cascade_batch(A, E[1], Sd * np.exp(-sigma ** 2 / 2), Pq, None)
ok("9a affine shortcut == direct mean-preserving computation", np.allclose(d_aff, d_dir, rtol=1e-6, atol=1e-12))
covs = []
for seed in range(40):
    rr = np.random.default_rng(1000 + seed)
    P = sample("flow", n, 0.6, rr, supply=supply, sections=sections)
    s_rnd = M[1] * rr.lognormal(-sigma ** 2 / 2, sigma, size=n)
    draws = cascade_batch(A, E[1], s_rnd[None, :] * rr.lognormal(0.0, sigma, size=(400, n)), P, None)
    d0 = cascade_batch(A, E[1], np.zeros((1, n)), P, None)
    covs.append(coverage_width(mean_preserving(draws, d0, sigma), M[1], tidx, 95)[0])
ok("9b random unbiased substitute gives near-nominal coverage", 88 <= np.mean(covs) <= 99, f"mean={np.mean(covs):.1f}%")
print("\nverification complete")
