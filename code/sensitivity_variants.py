"""80% coverage (400 seeds x 400 draws) and halving points for the sensitivity variants in Table 2.

Run from the repository root after sensitivity_analysis.py: python code/sensitivity_variants.py
"""
import sys,hashlib,json,os; HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE); sys.path.insert(0,HERE)
import sensitivity_analysis as a, numpy as np
n=64
def cov80(k,Sk,gsd=2.0,gp=None,seeds=400,draws=400):
    covs=[]
    for s in range(seeds):
        key=f"flow|{s}"
        rng=np.random.default_rng(int(hashlib.md5(key.encode()).hexdigest()[:8],16))
        o=a.full_order('flow',n,rng,supply=a.supply,sections=a.sections,advantage=np.zeros(n))
        P=a.sample_from_order(o,n,0.8)
        e=a.E[k].copy()
        if gp:
            r2=np.random.default_rng(int(hashlib.md5(f"pn|{gp}|{s}".encode()).hexdigest()[:8],16))
            e=e*r2.lognormal(0,np.log(gp),size=n)
        rm=np.random.default_rng(int(hashlib.md5((key+"|0.8|None|mc").encode()).hexdigest()[:8],16))
        noise=rm.lognormal(0,np.log(gsd),size=(draws,n))
        dr=a.cb(e,Sk[k][None,:]*noise,P)
        lo=np.percentile(dr,2.5,axis=0);hi=np.percentile(dr,97.5,axis=0)
        covs.append(np.mean((a.M[k][a.tidx]>=lo[a.tidx])&(a.M[k][a.tidx]<=hi[a.tidx]))*100)
    return float(np.mean(covs))
out={}
variants={'section':(a.S,None),'coarse':(a.groups_S('coarse'),None),'economy':(a.groups_S('economy'),None),
          'pn1.2':(a.S,1.2),'pn1.5':(a.S,1.5)}
for name,(Sk,gp) in variants.items():
    c=a.curve(0,Sk,'flow',gsd_primary=gp); med=np.median(c,axis=0)
    # participation needed to halve baseline-free floor: use own floor
    out[name]={'floor':float(med[0]),'halve':a.thresh(med),'med':[float(x) for x in med],'cov80':cov80(0,Sk,gp=gp)}
    # also halve relative to the baseline floor 13.85
    out[name]['halve_vs_base']=next((r for r,v in zip(a.RATES,med) if v<=13.848282/2),None)
    print(name,{k:v for k,v in out[name].items() if k!='med'},flush=True)
json.dump(out,open(os.path.join(ROOT,'data','sensitivity_variants.json'),'w'),indent=1)
