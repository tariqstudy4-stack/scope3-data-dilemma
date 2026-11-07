"""Re-score the motor vehicle industry (NACE C29) alone (automotive check, Section 4.5 of the manuscript).

Run from the repository root: python code/c29_check.py  -> data/c29_check.json
Flow-weighted adoption, converged chaining, 400 seeds; median absolute percentage error of C29 per rate.
"""
import sys, os, json, hashlib
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); sys.path.insert(0,HERE)
import numpy as np
from cascade import secondary_factors, true_pcf
from patterns import full_order, sample_from_order
d=np.load(os.path.join(ROOT,'data','matrices.npz'),allow_pickle=True)
A,E,Z=d['A'],d['E'],d['Z']; inds=list(d['industries']); n=len(inds); air=list(d['airpol'])
sections=np.array([c[0] for c in inds]); supply=Z.sum(axis=1)+1e-9
M=true_pcf(A,E); S=secondary_factors(M,inds); c29=inds.index('C29')
RATES=[0.0,0.05,0.10,0.20,0.40,0.60,0.80,1.00]
def conv(e,s_row,P):
    r=s_row.copy()
    for _ in range(200):
        rn=np.where(P,e+r@A,s_row)
        if np.max(np.abs(rn-r))<1e-12: r=rn;break
        r=rn
    return e+r@A
out={}
for k,pol in enumerate(air):
    ape=np.zeros((400,len(RATES)))
    for s in range(400):
        key=f"flow|{s}"; rng=np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8],16))
        o=full_order('flow',n,rng,supply=supply,sections=sections,advantage=np.zeros(n))
        for ri,r in enumerate(RATES):
            P=sample_from_order(o,n,r); pt=conv(E[k],S[k],P)
            ape[s,ri]=abs(pt[c29]-M[k][c29])/M[k][c29]*100
    out[str(pol)]=[round(float(x),2) for x in np.median(ape,axis=0)]
    print(pol,out[str(pol)])
json.dump(out,open(os.path.join(ROOT,'data','c29_check.json'),'w'),indent=1)
