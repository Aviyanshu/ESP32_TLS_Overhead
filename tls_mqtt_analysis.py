import pandas as pd, numpy as np, glob, os, json, math
from scipy.stats import mannwhitneyu, fisher_exact, spearmanr, median_abs_deviation as mad
rows=[]
for f in sorted(glob.glob('clean/*.csv')):
    reg,name=os.path.basename(f).split('__')
    d=pd.read_csv(f); d.columns=['seq','rtt','heap','rssi']+(['temp','wall'] if d.shape[1]==6 else ['wall'])
    d['regime']=reg; d['tls']='tls' in name; d['sensor']='temp' in name
    d['file']=name.replace('.csv',''); d['wall']=pd.to_datetime(d.wall)
    rows.append(d)
D=pd.concat(rows,ignore_index=True)
D['cond']=np.where(D.tls,'TLS','Plain'); D['track']=np.where(D.sensor,'Sensor','No-sensor')
D.to_pickle('D.pkl')
out={}
regs=['strong','medium','weak']
print('N',len(D), D.groupby(['cond']).size().to_dict())
# per cell
cells=[]
for s in (False,True):
  for r in regs:
    P=D[(D.regime==r)&(D.sensor==s)&(~D.tls)]; T=D[(D.regime==r)&(D.sensor==s)&(D.tls)]
    p,t=P.rtt.values,T.rtt.values
    u=mannwhitneyu(p,t,alternative='two-sided')
    # common-language effect: P(T>P)
    cl=(u.statistic)/(len(p)*len(t))  # U for first sample = P(plain>tls)+.5ties
    c=dict(track='Sensor' if s else 'No-sensor',regime=r,
      rssi_p=P.rssi.mean(),rssi_t=T.rssi.mean(),rssisd_p=P.rssi.std(),rssisd_t=T.rssi.std(),
      heap_p=P.heap.mean(),heap_t=T.heap.mean(),
      med_p=np.median(p),med_t=np.median(t),mad_p=mad(p,scale='normal'),mad_t=mad(t,scale='normal'),
      tm_p=pd.Series(p).sort_values().iloc[15:135].mean(),tm_t=pd.Series(t).sort_values().iloc[15:135].mean(),
      mean_p=p.mean(),mean_t=t.mean(),
      mw_p=u.pvalue,ps_plain_gt=cl,
      p95_p=np.percentile(p,95),p95_t=np.percentile(t,95),p99_p=np.percentile(p,99),p99_t=np.percentile(t,99),
      max_p=p.max(),max_t=t.max(),
      e300_p=(p>300).sum(),e300_t=(t>300).sum(),e500_p=(p>500).sum(),e500_t=(t>500).sum(),
      start_p=str(P.wall.min()),end_p=str(P.wall.max()),start_t=str(T.wall.min()),end_t=str(T.wall.max()))
    c['heap_ovh']=c['heap_p']-c['heap_t']; c['heap_pct']=100*c['heap_ovh']/c['heap_p']
    cells.append(c)
C=pd.DataFrame(cells); C.to_pickle('C.pkl')
pd.set_option('display.width',300); pd.set_option('display.max_columns',60)
print(C.round(3).to_string())
# thresholds pooled
P=D[~D.tls].rtt.values; T=D[D.tls].rtt.values
print('\nthreshold table')
thr=[]
for th in (150,200,300,400,500,1000):
    a,b=(T>th).sum(),(P>th).sum()
    rr=a/b; se=math.sqrt(1/a-1/900+1/b-1/900)
    thr.append(dict(th=th,tls=a,plain=b,rr=rr,lo=math.exp(math.log(rr)-1.96*se),hi=math.exp(math.log(rr)+1.96*se),p=fisher_exact([[a,900-a],[b,900-b]])[1]))
TH=pd.DataFrame(thr); print(TH.round(3)); TH.to_pickle('TH.pkl')
# files with events
print('\nevents >500 by file'); print(D[D.rtt>500].groupby(['regime','file']).size())
print('\nevents >300 by file'); print(D[D.rtt>300].groupby(['regime','file']).size().to_string())
print('files w >500 tls',D[(D.rtt>500)&D.tls].groupby(['regime','file']).ngroups,'plain',D[(D.rtt>500)&~D.tls].groupby(['regime','file']).ngroups)
# per cell direction at >500
# values above 250
print('\nvalues>250 sorted', sorted(D[D.rtt>250].rtt.tolist()))
print('values 200-1000:',sorted(D[(D.rtt>200)&(D.rtt<1000)].rtt.tolist()))
# autocorrelation lag1 per file
ac=[]
for (r,f),g in D.groupby(['regime','file']):
    x=g.sort_values('seq').rtt.values
    ac.append(spearmanr(x[:-1],x[1:]).statistic)
ac=np.array(ac); print('\nlag1 spearman per file: median %.3f, range %.3f..%.3f, n>0.3: %d of %d'%(np.median(ac),ac.min(),ac.max(),(np.abs(ac)>0.3).sum(),len(ac)))
# consecutive spikes
sp=0
for (r,f),g in D.groupby(['regime','file']):
    x=(g.sort_values('seq').rtt.values>300); sp+=np.sum(x[1:]&x[:-1])
print('consecutive >300 pairs',sp)
# seq continuity
print('all seq 1..50:',all((g.seq.values==np.arange(1,51)).all() for _,g in D.groupby(['regime','file'])))
print('rssi sd per file max',D.groupby(['regime','file']).rssi.std().max().round(2))
print('heap per-cond range',D.groupby('cond').heap.agg(['min','max','mean']))
print('heap overhead range',C.heap_ovh.min(),C.heap_ovh.max(),C.heap_pct.min(),C.heap_pct.max())
# temperatures
S=D[D.sensor]; print('temp range',S.temp.min(),S.temp.max(), 'step multiples of 1/16:', np.allclose((S.temp*16).round(1)%1,0,atol=0.2))
print('first/last wall',D.wall.min(),D.wall.max())
# median of sensor track minus nosensor
print('sensor-nosensor median diff', D[D.sensor].rtt.median()-D[~D.sensor].rtt.median())
# bonferroni
print('bonf',0.05/6)
# conditional binomial and per-regime

# ---- v4: context of slow round trips (exploratory) ----
from scipy.stats import mannwhitneyu as _mw
E=D.sort_values(['regime','file','seq']).reset_index(drop=True)
gg=E.groupby(['regime','file'])
E['rssi_dev']=E.rssi-gg.rssi.transform('median'); E['heap_dev']=E.heap-gg.heap.transform('median')
E['next_rtt']=gg.rtt.shift(-1)
S=E[E.rtt>250]; N=E[E.rtt<=250]
ctx=dict(n_slow=len(S), rssi_p=_mw(S.rssi_dev,N.rssi_dev).pvalue, rssi_dev_slow=S.rssi_dev.median(),
  next_med=S.next_rtt.median(), all_med=E.rtt.median(), seq_p=_mw(S.seq,N.seq).pvalue,
  heapdip_slow=int((S.heap_dev<-150).sum()), heapdip_all=int((E.heap_dev<-150).sum()),
  share_plain=E[(~E.tls)&(E.rtt>250)].rtt.sum()/E[~E.tls].rtt.sum(), share_tls=E[(E.tls)&(E.rtt>250)].rtt.sum()/E[E.tls].rtt.sum())
S=S.assign(cluster=np.where((S.rtt>=285)&(S.rtt<=385),'A: 291-379 ms',np.where((S.rtt>=1350)&(S.rtt<=1500),'B: 1358-1489 ms','other')))
CL=pd.crosstab([S.regime],[S.cluster,S.cond])
print('\nCONTEXT',{k:(round(v,3) if isinstance(v,float) else v) for k,v in ctx.items()})
print(CL)
import pickle; pickle.dump((ctx,S[['regime','track','cond','rtt','cluster']]),open('ctx.pkl','wb'))
