"""Makes the four report figures from D.pkl and TH.pkl (run tls_mqtt_analysis.py first).
Usage: python make_figures.py"""
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.stats import fisher_exact
import os, sys
RES = sys.argv[1] if len(sys.argv) > 1 else '.'
D=pd.read_pickle(os.path.join(RES,'D.pkl')); TH=pd.read_pickle(os.path.join(RES,'TH.pkl'))
plt.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'font.size':8,'axes.linewidth':0.6,'xtick.major.width':0.6,'ytick.major.width':0.6,'legend.fontsize':7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
P,T='#2A3990','#E8833A'; col={False:P,True:T}; rng=np.random.default_rng(1)
O='figures/'
os.makedirs(O, exist_ok=True)
# Fig1 RTT scatter, full width
fig,axes=plt.subplots(1,2,figsize=(7.1,2.5),sharey=True)
for ax,s in zip(axes,(False,True)):
    for i,r in enumerate(['strong','medium','weak']):
        for j,t in enumerate((False,True)):
            x=D[(D.regime==r)&(D.sensor==s)&(D.tls==t)].rtt.values; xp=i+(j-0.5)*0.36
            ax.scatter(xp+rng.uniform(-0.12,0.12,len(x)),x,s=3,color=col[t],alpha=0.55,linewidths=0,label=('TLS' if t else 'Plain') if (i==0 and s==False) else None)
            ax.hlines(np.median(x),xp-0.15,xp+0.15,color='black',lw=1.2,label='Median' if (i==0 and j==0 and s==False) else None)
    ax.axhline(300,color='gray',ls='--',lw=0.6)
    ax.set_yscale('log'); ax.set_ylim(3,2500); ax.set_xticks(range(3)); ax.set_xticklabels(['Near','Medium','Far'])
    ax.set_title('Sensor payload' if s else 'Dummy payload',fontsize=8)
axes[0].set_ylabel('Round-trip time (ms, log)'); axes[0].set_yticks([5,10,30,100,300,1000]); axes[0].set_yticklabels(['5','10','30','100','300','1000'])
fig.legend(loc='upper center',ncol=3,frameon=False,markerscale=3,bbox_to_anchor=(0.5,1.02))
fig.tight_layout(rect=(0,0,1,0.92)); fig.savefig(O+'fig_rtt.png', dpi=200); plt.close()
# Fig2 cutoffs
fig,ax=plt.subplots(figsize=(3.45,2.1)); x=np.arange(len(TH)); w=0.38
ax.bar(x-w/2,TH.plain,w,color=P,label='Plain'); ax.bar(x+w/2,TH.tls,w,color=T,label='TLS')
for xi,a,b,p in zip(x,TH.tls,TH.plain,TH.p):
    ax.text(xi+w/2,a+0.4,str(int(a)),ha='center',fontsize=6.5); ax.text(xi-w/2,b+0.4,str(int(b)),ha='center',fontsize=6.5)
ax.set_xticks(x); ax.set_xticklabels([f'>{int(t)}\np={p:.3f}' for t,p in zip(TH.th,TH.p)],fontsize=6.5)
ax.set_ylabel('Slow trips (of 900)'); ax.set_xlabel('Cutoff (ms) and Fisher exact p'); ax.legend(frameon=False); ax.set_ylim(0,31)
fig.tight_layout(); fig.savefig(O+'fig_cutoffs.png', dpi=200); plt.close()
# Fig3 near/away
fig,ax=plt.subplots(figsize=(3.45,1.9))
grp=[('Near\n(300 per protocol)',['strong']),('Medium + far\n(600 per protocol)',['medium','weak'])]
for i,(lab,regs) in enumerate(grp):
    s=D[D.regime.isin(regs)]; t=(s[s.tls].rtt>300).sum(); p=(s[~s.tls].rtt>300).sum()
    ax.bar(i-0.18,p,0.36,color=P,label='Plain' if i==0 else None); ax.bar(i+0.18,t,0.36,color=T,label='TLS' if i==0 else None)
    ax.text(i-0.18,p+0.4,str(p),ha='center',fontsize=7); ax.text(i+0.18,t+0.4,str(t),ha='center',fontsize=7)
ax.set_xticks([0,1]); ax.set_xticklabels([g[0] for g in grp]); ax.set_ylabel('Trips over 300 ms'); ax.set_ylim(0,24); ax.legend(frameon=False,loc='upper left')
fig.tight_layout(); fig.savefig(O+'fig_nearfar.png', dpi=200); plt.close()
# Fig4 clusters
S=D[D.rtt>250]; fig,ax=plt.subplots(figsize=(3.45,1.9)); bins=np.arange(250,1600,50)
ax.hist([S[~S.tls].rtt,S[S.tls].rtt],bins=bins,stacked=True,color=[P,T],label=['Plain','TLS'],edgecolor='white',linewidth=0.4)
ax.set_xlabel('Round-trip time (ms), all 28 trips over 250 ms'); ax.set_ylabel('Trips'); ax.legend(frameon=False,loc='center'); ax.set_ylim(0,10.5); ax.set_yticks([0,2,4,6,8,10])
ax.text(255,7.6,'291–379 ms (11 trips)',ha='left',fontsize=6.5); ax.text(1500,8.6,'1358–1489 ms (12 trips)',ha='right',fontsize=6.5)
fig.tight_layout(); fig.savefig(O+'fig_clusters.png', dpi=200); plt.close()
print('ok')
