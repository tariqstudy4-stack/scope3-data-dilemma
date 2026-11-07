"""Sensitivity and bootstrap analysis behind Table 2 and Table S3 of the revised manuscript.

Run from the repository root: python code/sensitivity_analysis.py
Writes data/sensitivity_base.npz, data/sensitivity_boot.json, data/sensitivity_variants.json
(floor, halving point against the variant's own floor and against the baseline floor, 80% coverage).
"""
import sys, hashlib, json, time, os
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)
import numpy as np
from cascade import secondary_factors, true_pcf, ape_per_target, mape, _SUPERSECTION_MEMBERS
from patterns import full_order, sample_from_order

d=np.load(os.path.join(ROOT,'data','matrices.npz'),allow_pickle=True)
A,E,Z=d['A'],d['E'],d['Z']; inds=list(d['industries']); n=64
manuf=list(d['manuf']); tidx=np.array([inds.index(c) for c in manuf])
sections=np.array([c[0] for c in inds]); supply=Z.sum(axis=1)+1e-9
M=true_pcf(A,E); S=secondary_factors(M,inds); air=list(d['airpol'])
RATES=[0.0,0.05,0.10,0.20,0.40,0.60,0.80,1.00]
SEEDS=400

def cb(e,Sd,P,tiers=None):
    R=Sd.copy()
    for _ in range(200):
        Rn=np.where(P[None,:],e[None,:]+R@A,Sd)
        if np.max(np.abs(Rn-R))<1e-12: R=Rn;break
        R=Rn
    return e[None,:]+R@A

def groups_S(level):
    S2=np.zeros_like(M)
    if level=='section': return S
    if level=='coarse':
        g=np.array(['A' if c[0]=='A' else ('IND' if c[0] in 'BCDEF' else 'SERV') for c in inds])
    else: g=np.array(['ALL']*n)
    for j in range(n):
        sib=[i for i in range(n) if g[i]==g[j] and i!=j]
        S2[:,j]=M[:,sib].mean(axis=1)
    return S2

def order_for(pattern,seed):
    key=f"{pattern}|{seed}"
    rng=np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8],16))
    return full_order(pattern,n,rng,supply=supply,sections=sections,advantage=np.zeros(n))

def curve(k,Sk,pattern='flow',gsd_primary=None,seeds=SEEDS):
    """returns array seeds x rates of MAPE (converged)"""
    out=np.zeros((seeds,len(RATES)))
    for s in range(seeds):
        o=order_for(pattern,s)
        e=E[k].copy()
        if gsd_primary:
            rng=np.random.default_rng(int(hashlib.md5(f"pn|{gsd_primary}|{s}".encode()).hexdigest()[:8],16))
            e=e*rng.lognormal(0,np.log(gsd_primary),size=n)
        for ri,r in enumerate(RATES):
            P=sample_from_order(o,n,r)
            pt=cb(e,Sk[k][None,:],P)[0]
            out[s,ri]=mape(pt,M[k],tidx)
    return out

def thresh(med):
    fl=med[0]
    for r,v in zip(RATES,med):
        if v<=fl/2: return r
    return None

def coverage80(k,Sk,gsd=2.0,gsd_primary=None,seeds=60,draws=200):
    covs=[]
    for s in range(seeds):
        o=order_for('flow',s); P=sample_from_order(o,n,0.8)
        e=E[k].copy()
        if gsd_primary:
            rng=np.random.default_rng(int(hashlib.md5(f"pn|{gsd_primary}|{s}".encode()).hexdigest()[:8],16))
            e=e*rng.lognormal(0,np.log(gsd_primary),size=n)
        rng=np.random.default_rng(int(hashlib.md5(f"cov|{s}".encode()).hexdigest()[:8],16))
        noise=rng.lognormal(0,np.log(gsd),size=(draws,n))
        dr=cb(e,Sk[k][None,:]*noise,P)
        lo=np.percentile(dr,2.5,axis=0);hi=np.percentile(dr,97.5,axis=0)
        covs.append(np.mean((M[k][tidx]>=lo[tidx])&(M[k][tidx]<=hi[tidx]))*100)
    return float(np.mean(covs))

if __name__=='__main__':
    t0=time.time(); res={}
    # baseline all indicators, three patterns -> bootstrap thresholds
    base={}
    for k,pol in enumerate(air):
        base[pol]={}
        for pat in ('random','flow','cluster'):
            base[pol][pat]=curve(k,S,pat)
        print(pol,'base done',round(time.time()-t0),flush=True)
    np.savez(os.path.join(ROOT,'data','sensitivity_base.npz'),**{f"{p}|{q}":v for p in base for q,v in base[p].items()})
    # bootstrap
    rng=np.random.default_rng(1)
    boot={}
    for pol in air:
        c=base[pol]['flow']; ths=[]
        for b in range(2000):
            idx=rng.integers(0,SEEDS,SEEDS)
            t=thresh(np.median(c[idx],axis=0)); ths.append(-1 if t is None else t)
        vals,cnt=np.unique(ths,return_counts=True)
        boot[pol]={'point':thresh(np.median(c,axis=0)),'floor':float(np.median(c[:,0])),
          'dist':{str(v):float(cn/len(ths)) for v,cn in zip(vals,cnt)},
          'ci':[float(np.percentile(ths,2.5)),float(np.percentile(ths,97.5))]}
        # bootstrap CI on floor and on 60% mape
    json.dump(boot,open(os.path.join(ROOT,'data','sensitivity_boot.json'),'w'),indent=1)
    print(json.dumps(boot,indent=1))
    # Fig2 5% point check
    f2={}
    for pat in ('random','flow','cluster'):
        f2[pat]=[float(v) for v in np.median(base['GHG'][pat],axis=0)]
        f2[pat+'_iqr']=[[float(np.percentile(base['GHG'][pat][:,i],25)),float(np.percentile(base['GHG'][pat][:,i],75))] for i in range(len(RATES))]
    json.dump(f2,open(os.path.join(ROOT,'data','fig2_medians_iqr.json'),'w'),indent=1)
    print('fig2',json.dumps({k:[round(x,2) for x in v] for k,v in f2.items() if 'iqr' not in k}))
    # sensitivity (GHG, flow)
    sens={}
    for name,lvl in (('section',None),('coarse','coarse'),('economy','economy')):
        Sk=S if lvl is None else groups_S(lvl)
        c=curve(0,Sk); med=np.median(c,axis=0)
        sens[name]={'floor':float(med[0]),'halve':thresh(med),'mape20':float(med[3]),'cov80':coverage80(0,Sk)}
        print(name,sens[name],round(time.time()-t0),flush=True)
    for g in (1.2,1.5):
        c=curve(0,S,gsd_primary=g,seeds=200); med=np.median(c,axis=0)
        sens[f'primary_noise_{g}']={'floor':float(med[0]),'halve':thresh(med),'mape20':float(med[3]),'cov80':coverage80(0,S,gsd_primary=g)}
        print(g,sens[f'primary_noise_{g}'],flush=True)
    json.dump(sens,open(os.path.join(ROOT,'data','sensitivity_variants_quick.json'),'w'),indent=1)
