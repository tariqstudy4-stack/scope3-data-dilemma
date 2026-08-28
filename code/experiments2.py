"""Revised experiment grid: 400 seeds, nested/paired participant order
(shared across indicators and tier depths for a given pattern+seed), and a
fourth (strategic / MNAR) adoption pattern. Chunked by indicator via CLI
arg so each chunk finishes inside a single shell call.

Usage: python3 experiments2.py <indicator_index 0-3>
"""
import hashlib
import json
import sys
import time

import numpy as np

from cascade import secondary_factors, true_pcf, mape, ranking_flips, ape_per_target
from patterns import PATTERNS, full_order, sample_from_order

RATES = [0.0, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00]
TIERS = [1, 2, 3, None]
SEEDS = list(range(400))
GSD = 2.0
N_DRAWS = 400
NOMINAL = 95


def cascade_batch(A, e, S_draws, P, tiers):
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
    only_k = int(sys.argv[1]) if len(sys.argv) > 1 else None

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
    sigma = np.log(GSD)
    airpol = list(d["airpol"])

    # composite, indicator-averaged "looks better than the database
    # default" advantage score, used only by the strategic pattern. Built
    # from ALL four indicators so the disclosure decision is not itself
    # indicator-specific (a supplier decides once whether to join, not
    # once per pollutant it is scored on).
    adv_parts = []
    for k in range(len(airpol)):
        num = S[k] - M[k]
        z = (num - num.mean()) / (num.std() + 1e-12)
        adv_parts.append(z)
    advantage = np.mean(adv_parts, axis=0)

    kmin, kmax = (only_k, only_k + 1) if only_k is not None else (0, len(airpol))

    rows = []
    t0 = time.time()
    for k in range(kmin, kmax):
        pol = airpol[k]
        e, s_row, m = E[k], S[k], M[k]
        for pattern in PATTERNS:
            for seed in SEEDS:
                key = f"{pattern}|{seed}"
                rng = np.random.default_rng(int(
                    hashlib.md5(key.encode()).hexdigest()[:8], 16))
                order = full_order(pattern, n, rng, supply=supply,
                                    sections=sections, advantage=advantage)
                for rate in RATES:
                    P = sample_from_order(order, n, rate)
                    for tiers in TIERS:
                        pt = cascade_batch(A, e, s_row[None, :], P, tiers)[0]
                        rng_mc = np.random.default_rng(int(hashlib.md5(
                            (key + f"|{rate}|{tiers}|mc").encode())
                            .hexdigest()[:8], 16))
                        noise = rng_mc.lognormal(0.0, sigma, size=(N_DRAWS, n))
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
                        ape = ape_per_target(pt, m, tidx)
                        rows.append(dict(
                            indicator=str(pol), pattern=pattern, rate=rate,
                            tiers=(0 if tiers is None else tiers), seed=seed,
                            mape=mape(pt, m, tidx),
                            p90=float(np.percentile(ape, 90)),
                            maxape=float(np.max(ape)),
                            flips=flips, n_pairs=npairs, coverage=cov,
                            rel_width=width, n_participants=int(P.sum()),
                            pds=float(np.mean(pds[tidx])),
                            flow_share=float(supply[P].sum() / supply.sum()),
                        ))
        print(f"{pol}: done ({time.time()-t0:.0f}s, {len(rows)} rows)",
              flush=True)

    suffix = f"_{only_k}" if only_k is not None else ""
    with open(f"data/results_400{suffix}.json", "w") as f:
        json.dump(rows, f)
    print(f"TOTAL {len(rows)} conditions in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
