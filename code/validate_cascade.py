import numpy as np
from cascade import (cascade_reports, target_pcf, true_pcf,
                     secondary_factors, mape, ranking_flips)

d = np.load("data/matrices.npz", allow_pickle=True)
A, E = d["A"], d["E"]
inds = list(d["industries"]); manuf = list(d["manuf"])
tidx = np.array([inds.index(c) for c in manuf])
M = true_pcf(A, E)
S = secondary_factors(M, inds)

for k, pol in enumerate(d["airpol"]):
    e, s, m = E[k], S[k], M[k]
    # V1: full participation, converged -> exact truth
    r = cascade_reports(A, e, s, np.ones(len(inds), bool), None)
    err_full = np.max(np.abs(target_pcf(A, e, r) - m) / np.maximum(m, 1e-30))
    # V2: zero participation -> primary direct + secondary upstream (PACT floor)
    r0 = cascade_reports(A, e, s, np.zeros(len(inds), bool), None)
    p0 = target_pcf(A, e, r0)
    expected0 = e + s @ A
    err_zero = np.max(np.abs(p0 - expected0))
    # V3: tier monotonicity of information: T=1 equals zero-participation
    #     when no one participates
    r1 = cascade_reports(A, e, s, np.zeros(len(inds), bool), 1)
    err_t1 = np.max(np.abs(target_pcf(A, e, r1) - expected0))
    print(f"{pol}: full-participation max rel err = {err_full:.2e}  "
          f"zero-participation identity = {err_zero:.2e}  tier1 = {err_t1:.2e}")
    print(f"   zero-participation MAPE on 19 targets = "
          f"{mape(p0, m, tidx):.2f}%   flips = {ranking_flips(p0, m, tidx)}")
