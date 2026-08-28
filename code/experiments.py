"""Full experiment grid for the PCF cascade benchmark."""
import hashlib
import json
import time

import numpy as np

from cascade import (secondary_factors, true_pcf, mape, ranking_flips)
from patterns import PATTERNS, sample

RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
TIERS = [1, 2, 3, None]          # None = converged (infinite chaining)
SEEDS = list(range(10))
GSD = 2.0                        # pedigree-style geometric SD on secondary data
N_DRAWS = 400
NOMINAL = 95


def cascade_batch(A, e, S_draws, P, tiers):
    """Vectorized cascade over Monte Carlo draws.
    S_draws: (d, n) secondary factors per draw. Returns target PCFs (d, n)."""
    R = S_draws.copy()
    it = 200 if tiers is None else tiers
    for _ in range(it):
        R_new = np.where(P[None, :], e[None, :] + R @ A, S_draws)
        if tiers is None and np.max(np.abs(R_new - R)) < 1e-12:
            R = R_new
            break
        R = R_new
    return e[None, :] + R @ A


def primary_data_share(A, e, s_row, P, tiers):
    """PACT Methodology 4.2.2 primaryDataShare of each target PCF.

    Tracks, through the same cascade recursion, how much of every reported
    value is ultimately derived from secondary (database) data. For a
    non-participant the entire handed-over value is secondary; for a
    participant only the secondary content of its upstream inputs is.
    """
    r = s_row.copy()
    sec = s_row.copy()                    # secondary mass inside each report
    it = 200 if tiers is None else tiers
    for _ in range(it):
        sec_hand = np.where(P, sec, s_row)    # what suppliers hand over
        r_new = np.where(P, e + r @ A, s_row)
        sec_new = np.where(P, sec_hand @ A, s_row)
        if tiers is None and np.max(np.abs(r_new - r)) < 1e-12:
            r, sec = r_new, sec_new
            break
        r, sec = r_new, sec_new
    hand = np.where(P, r, s_row)          # values suppliers hand to the target
    sec_hand = np.where(P, sec, s_row)    # secondary mass inside those values
    pcf = e + hand @ A
    sec_target = sec_hand @ A
    with np.errstate(divide="ignore", invalid="ignore"):
        pds = np.where(pcf > 1e-30, 1.0 - sec_target / pcf, 0.0)
    return pds


def main():
    d = np.load("data/matrices.npz", allow_pickle=True)
    A, E, Z = d["A"], d["E"], d["Z"]
    inds = list(d["industries"])
    n = len(inds)
    manuf = list(d["manuf"])
    tidx = np.array([inds.index(c) for c in manuf])
    sections = np.array([c[0] for c in inds])
    supply = Z.sum(axis=1) + 1e-9   # total intermediate supply per industry
    M = true_pcf(A, E)
    S = secondary_factors(M, inds)
    sigma = np.log(GSD)

    rows = []
    t0 = time.time()
    for k, pol in enumerate(d["airpol"]):
        e, s_row, m = E[k], S[k], M[k]
        for pattern in PATTERNS:
            for rate in RATES:
                for tiers in TIERS:
                    for seed in SEEDS:
                        key = f"{k}|{pattern}|{rate}|{tiers}|{seed}"
                        rng = np.random.default_rng(int(
                            hashlib.md5(key.encode()).hexdigest()[:8], 16))
                        P = sample(pattern, n, rate, rng,
                                   supply=supply, sections=sections)
                        # point estimate: secondary factors at their central value
                        pt = cascade_batch(A, e, s_row[None, :], P, tiers)[0]
                        # Monte Carlo: lognormal noise on secondary factors only
                        noise = rng.lognormal(0.0, sigma, size=(N_DRAWS, n))
                        draws = cascade_batch(A, e, s_row[None, :] * noise,
                                              P, tiers)
                        lo = np.percentile(draws, (100 - NOMINAL) / 2, axis=0)
                        hi = np.percentile(draws, 100 - (100 - NOMINAL) / 2,
                                           axis=0)
                        cov = float(np.mean((m[tidx] >= lo[tidx])
                                            & (m[tidx] <= hi[tidx])) * 100)
                        width = float(np.median(
                            (hi[tidx] - lo[tidx]) / np.maximum(m[tidx], 1e-30)))
                        flips, npairs = ranking_flips(pt, m, tidx)
                        pds = primary_data_share(A, e, s_row, P, tiers)
                        rows.append(dict(
                            indicator=str(pol), pattern=pattern, rate=rate,
                            tiers=(0 if tiers is None else tiers), seed=seed,
                            mape=mape(pt, m, tidx), flips=flips,
                            n_pairs=npairs, coverage=cov, rel_width=width,
                            n_participants=int(P.sum()),
                            pds=float(np.mean(pds[tidx])),
                            flow_share=float(supply[P].sum() / supply.sum()),
                        ))
        print(f"{pol}: done ({time.time()-t0:.0f}s, {len(rows)} rows)")

    with open("data/results.json", "w") as f:
        json.dump(rows, f)
    print(f"TOTAL {len(rows)} conditions in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
