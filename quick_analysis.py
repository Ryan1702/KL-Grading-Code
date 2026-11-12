import json, re
from pathlib import Path
import numpy as np
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
R = Path(__file__).resolve().parent
O = R/"final_model"
z = np.load(O/"preds.npz"); y,p,prob = z["y"], z["pred"], z["prob"]
files=[l.strip() for l in open(R/"cache"/"test_files.txt")]
pids=np.array([re.match(r"(\d+)", Path(f).name).group(1) for f in files])
def wl(k,n,z=1.96):
    ph=k/n; d=1+z*z/n; c=ph+z*z/(2*n); h=z*np.sqrt(ph*(1-ph)/n+z*z/(4*n*n)); return [(c-h)/d,(c+h)/d]
N=len(y); C=confusion_matrix(y,p); acc=(y==p).mean()
aucs=[roc_auc_score((y==i).astype(int), prob[:,i]) for i in range(5)]
res=dict(n=N, correct=int((y==p).sum()), accuracy=float(acc), acc_ci=wl(int((y==p).sum()),N),
    macro_f1=float(f1_score(y,p,average="macro")), macro_precision=float(precision_score(y,p,average="macro")),
    macro_recall=float(recall_score(y,p,average="macro")),
    kappa_quadratic=float(cohen_kappa_score(y,p,weights="quadratic")),
    per_class={str(i): dict(recall=float(recall_score(y,p,labels=[i],average="macro")),
        rec_ci=wl(int(C[i,i]),int(C[i].sum())), precision=float(precision_score(y,p,labels=[i],average="macro")),
        f1=float(f1_score(y,p,labels=[i],average="macro")), auc=float(aucs[i])) for i in range(5)},
    macro_auc=float(np.mean(aucs)), confusion=C.tolist())
off=C.copy(); np.fill_diagonal(off,0)
adj=sum(off[i,j] for i in range(5) for j in range(5) if abs(i-j)==1)
res.update(errors=int(off.sum()), adjacent=int(adj), far=int(off.sum()-adj))
def b(lo,hi):
    tp=C[lo:hi+1,lo:hi+1].sum(); fn=C[lo:hi+1].sum()-tp; fp=C[:,lo:hi+1].sum()-tp; tn=N-tp-fn-fp
    return dict(sens=float(tp/(tp+fn)), spec=float(tn/(tn+fp)), acc=float((tp+tn)/N), tp=int(tp), fn=int(fn), fp=int(fp), tn=int(tn))
res["kl_ge2"]=b(2,4); res["kl_ge3"]=b(3,4)
tier=C[0:2,0:2].sum()+C[2,2]+C[3:5,3:5].sum(); res["three_tier"]=dict(correct=int(tier), acc=float(tier/N))
rng=np.random.default_rng(42); ug=np.unique(pids); idx={g:np.where(pids==g)[0] for g in ug}
st={k:[] for k in ["accuracy","macro_f1","qwk","macro_auc"]}
for _ in range(2000):
    pick=rng.choice(ug,len(ug),replace=True); ii=np.concatenate([idx[g] for g in pick]); yy,pp,pr=y[ii],p[ii],prob[ii]
    if len(np.unique(yy))<5: continue
    st["accuracy"].append(accuracy_score(yy,pp)); st["macro_f1"].append(f1_score(yy,pp,average="macro"))
    st["qwk"].append(cohen_kappa_score(yy,pp,weights="quadratic")); st["macro_auc"].append(roc_auc_score(yy,pr,multi_class="ovr",average="macro"))
res["cluster_bootstrap"]={k:[float(np.percentile(v,2.5)),float(np.percentile(v,97.5))] for k,v in st.items()}
res["n_patients"]=int(len(ug))
(O/"analysis.json").write_text(json.dumps(res,indent=2))
print(json.dumps({k:res[k] for k in ["accurate","accuracy","acc_ci","macro_f1","kappa_quadratic","macro_auc","cluster_bootstrap"] if k in res},indent=1))
print("errors",res["errors"],"adj",res["adjacent"],"far",res["far"])
