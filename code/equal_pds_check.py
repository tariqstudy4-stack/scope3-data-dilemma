"""Equal-declared-PDS, cross-adoption-pattern comparison.

Reviewer-requested analysis (Domain / Perspective / Devil's Advocate,
independently): PACT's own PDS definition (Methodology 4.2.2) is already
emissions-weighted. The paper's headline "recruitment order matters more
than headcount" claim is based on comparing patterns at matched
PARTICIPATION RATE (fraction of industries onboarded), not at matched
DECLARED PDS. Since flow-weighted adoption reaches a higher PDS than
random/cluster adoption at the same raw participation rate (by
construction -- it recruits high-output-share suppliers first), part of
flow-weighted's apparent accuracy advantage could be a restatement of
"higher PDS is more accurate", not independent evidence that recruitment
PATTERN matters beyond what PDS already captures.

This script re-plots accuracy against the REALIZED declared PDS instead of
against the raw rate, separately for each pattern, and compares patterns
at matched PDS levels. If the curves collapse onto each other once
plotted against PDS, pattern does not matter beyond PDS (supports the
circularity concern). If flow-weighted keeps a real accuracy advantage
over random/cluster even at the same PDS, that is genuine evidence that
network configuration matters beyond participation share alone.

Converged chaining only (T=None), matching Fig. 2 / Table 1 / the
headline claims. Point estimates only (no Monte Carlo coverage sampling)
since PDS/MAPE are what's needed here -- this keeps runtime low enough to
run interactively instead of the full ~50 min/indicator 400-seed grid.
"""
import hashlib
import json
import time

import numpy as np

from cascade import secondary_factors, true_pcf, mape
from patterns import sample

RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
PATTERNS = ("random", "flow", "cluster")
N_SEEDS = 400
TIERS = None  # converged


def cascade_point(A, e, s_row, P, tiers):
    r = s_row.copy()
    it = 200 if tiers is None else tiers
    for _ in range(it):
        r_new = np.where(P, e + r @ A, s_row)
        if tiers is None and np.max(np.abs(r_new - r)) < 1e-12:
            r = r_new
            break
        r = r_new
    return e + r @ A


def primary_data_share(A, e, s_row, P, tiers):
    r = s_row.copy()
    sec = s_row.copy()
    it = 200 if tiers is None else tiers
    for _ in range(it):
        sec_hand = np.where(P, sec, s_row)
        r_new = np.where(P, e + r @ A, s_row)
        sec_new = np.where(P, sec_hand @ A, s_row)
        if tiers is None and np.max(np.abs(r_new - r)) < 1e-12:
            r, sec = r_new, sec_new
            break
        r, sec = r_new, sec_new
    hand = np.where(P, r, s_row)
    sec_hand = np.where(P, sec, s_row)
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
    supply = Z.sum(axis=1) + 1e-9
    M = true_pcf(A, E)
    S = secondary_factors(M, inds)

    rows = []
    t0 = time.time()
    for k, pol in enumerate(d["airpol"]):
        e, s_row, m = E[k], S[k], M[k]
        for pattern in PATTERNS:
            for rate in RATES:
                for seed in range(N_SEEDS):
                    key = f"eqpds|{k}|{pattern}|{rate}|{seed}"
                    rng = np.random.default_rng(int(
                        hashlib.md5(key.encode()).hexdigest()[:8], 16))
                    P = sample(pattern, n, rate, rng,
                               supply=supply, sections=sections)
                    pt = cascade_point(A, e, s_row, P, TIERS)
                    pds_vec = primary_data_share(A, e, s_row, P, TIERS)
                    rows.append(dict(
                        indicator=str(pol), pattern=pattern, rate=rate,
                        seed=seed,
                        mape=mape(pt, m, tidx),
                        pds=float(np.mean(pds_vec[tidx])),
                    ))
        print(f"{pol}: done ({time.time()-t0:.0f}s, {len(rows)} rows)")

    with open("data/equal_pds_check.json", "w") as f:
        json.dump(rows, f)
    print(f"TOTAL {len(rows)} rows in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
