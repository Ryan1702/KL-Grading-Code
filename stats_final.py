"""Final statistics: 5,000-resample cluster bootstrap + cluster-level sign-flip permutation test."""
import json, re
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, roc_auc_score

ROOT=Path(__file__).resolve().parent
FM=ROOT/"final_model"; BL=ROOT/"baselines"
files=[l.strip() for l in open(ROOT/"cache"/"test_files.txt")]
pids=np.array([re.match(r"(\d+)",Path(f).name).group(1) for f in files])
ug=np.unique(pids); idx={g:np.where(pids==g)[0] for g in ug}

z=np.load(FM/"preds.npz"); y=z["y"]
models={"ResNet-50":(z["pred"],z["prob"])}
for name,label in [("resnet18","ResNet-18"),("resnet34","ResNet-34"),("mobilenet_v2","MobileNetV2")]:
    d=np.load(BL/f"{name}_preds.npz"); models[label]=(d["pred"],d["prob"])

def metrics(yy,p,pr):
    return dict(accuracy=accuracy_score(yy,p), macro_f1=f1_score(yy,p,average="macro"),
                qwk=cohen_kappa_score(yy,p,weights="quadratic"),
                macro_auc=roc_auc_score(yy,pr,multi_class="ovr",average="macro"))

main_p,main_pr=models["ResNet-50"]
B=5000; rng=np.random.default_rng(2026)
boot={k:[] for k in ["accuracy","macro_f1","qwk","macro_auc"]}
for _ in range(B):
    pick=rng.choice(ug,len(ug),replace=True); ii=np.concatenate([idx[g] for g in pick])
    yy=y[ii]; m=metrics(yy,main_p[ii],main_pr[ii])
    for k in boot: boot[k].append(m[k])
ci={k:[float(np.percentile(v,2.5)),float(np.percentile(v,97.5))] for k,v in boot.items()}

# cluster-level sign-flip permutation for accuracy differences
def cluster_perm(p_base, n_perm=10000, seed=7):
    a=(main_p==y).astype(float); b=(p_base==y).astype(float)
    diff=np.array([ (a[ii]-b[ii]).mean() for ii in idx.values() ])
    obs=diff.mean(); r=np.random.default_rng(seed); cnt=0
    for _ in range(n_perm):
        s=r.choice([-1.0,1.0],len(diff)); cnt += abs((diff*s).mean())>=abs(obs)
    return float(obs), float((cnt+1)/(n_perm+1))

comp={}
for label,(p,pr) in models.items():
    if label=="ResNet-50": continue
    obs,pv=cluster_perm(p)
    comp[label]=dict(acc_diff_full=float(metrics(y,main_p,main_pr)["accuracy"]-metrics(y,p,pr)["accuracy"]),
                     cluster_perm_obs=obs, cluster_perm_p=pv)

out=dict(bootstrap=dict(n_resamples=B, seed=2026, unit="file identifier", interval="percentile",
                        point=metrics(y,main_p,main_pr), ci=ci),
         permutation=comp)
json.dump(out,open(FM/"stats_final.json","w"),indent=2)
print("bootstrap CI:", {k:[round(100*x,1) if k in ("accuracy","macro_auc") else round(x,3) for x in v] for k,v in ci.items()})
for k,v in comp.items(): print(k, "accDiff", round(v["acc_diff_full"],4), "perm p", round(v["cluster_perm_p"],4))
