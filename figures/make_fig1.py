"""Fig. 1 of the manuscript: framework of the study in six steps (schematic). Run from the repository root:
python figures/make_fig1.py -> figures/fig1_framework.png"""
import os
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams.update({'font.family':'DejaVu Sans','mathtext.fontset':'dejavusans'})
fig,ax=plt.subplots(figsize=(3.4,1.85),dpi=300); ax.set_xlim(0,10); ax.set_ylim(0.5,10); ax.axis('off')
def box(x,y,w,h,t,c,fs=4.9):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.02,rounding_size=0.2',fc=c,ec='none'))
    ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs,color='white',linespacing=1.25)
def arr(x1,y1,x2,y2,ls='-'):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=5,lw=.8,color='#444',linestyle=ls))
L,Rr=.7,5.35; W=4.45
box(.7,8.55,9.1,1.35,'1  INPUTS: Eurostat input-output table (64 industries)\nand air emission accounts, EU-27, 2022','#5B6770')
box(L,5.95,W,2.0,'2  GROUND TRUTH\n$\\mathbf{A}=\\mathbf{Z}/\\mathbf{x}$,  $\\mathbf{E}=\\mathbf{F}/\\mathbf{x}$\n$\\mathbf{m}=\\mathbf{E}(\\mathbf{I}-\\mathbf{A})^{-1}$','#0072B2')
box(Rr,5.95,W,2.0,'3  SECONDARY FACTORS\n$s_j$ = mean true intensity of\nsection siblings, $j$ left out','#D55E00')
box(L,3.45,W,2.0,'4  PARTICIPATION\nrandom, flow, cluster\nrate 0 to 100%, 400 seeds','#8E44AD')
box(Rr,3.45,W,2.0,'5  CASCADE, DEPTH $T$\nparticipant: $r_j=e_j+\\Sigma_i A_{ij}r_i$\nother: $r_j=s_j$','#009E73',fs=4.7)
box(.7,0.7,9.1,2.25,'6  OUTPUTS, COMPARED WITH $\\mathbf{m}$\nmedian error, 95% interval coverage,\nranking reversals, primary data share','#5B6770')
arr(2.9,8.45,2.9,7.95); arr(7.5,8.45,7.5,7.95); arr(7.5,5.95,7.5,5.45); arr(L+W,4.45,Rr,4.45); arr(7.5,3.45,7.5,2.95)
ax.plot([L,.3,.3],[6.95,6.95,1.8],color='#0072B2',lw=.8,ls='--'); arr(.3,1.8,.7,1.8,ls='--')
plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'fig1_framework.png'),bbox_inches='tight',pad_inches=.03); plt.close()
