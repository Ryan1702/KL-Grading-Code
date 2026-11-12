"""Calibration analysis: ECE, Brier, reliability diagram, temperature scaling fitted on the validation set."""
import json
from pathlib import Path
import numpy as np, torch, torch.nn as nn, torchvision.models as tv_models
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"final_model"; FIG=OUT/"figures"
CACHE=ROOT/"cache"; DEVICE=torch.device("mps" if torch.backends.mps.is_available() else "cpu")
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)

z=np.load(OUT/"preds.npz"); y,p,prob=z["y"],z["pred"],z["prob"]

def ece(prob,y,n_bins=15):
    conf=prob.max(1); pred=prob.argmax(1); acc=(pred==y).astype(float)
    bins=np.linspace(0,1,n_bins+1); e=0.0
    for i in range(n_bins):
        m=(conf>bins[i])&(conf<=bins[i+1])
        if m.sum()>0: e+=m.mean()*abs(acc[m].mean()-conf[m].mean())
    return float(e)

def brier(prob,y):
    oh=np.zeros_like(prob); oh[np.arange(len(y)),y]=1
    return float(np.mean(np.sum((prob-oh)**2,axis=1)))

# validation probabilities for temperature fitting
m=tv_models.resnet50(weights=None); m.fc=nn.Linear(m.fc.in_features,5)
m.load_state_dict(torch.load(OUT/"best_image_only.pth",map_location="cpu")); m.to(DEVICE).eval()
Xva=np.load(CACHE/"val.npy",mmap_mode="r"); yva=np.load(CACHE/"val_labels.npy")
logits=[]
with torch.no_grad():
    for k in range(0,len(yva),64):
        xs=np.array(Xva[k:k+64]).astype(np.float32)/255.0
        xs=(xs-MEAN)/STD
        t=torch.from_numpy(xs.transpose(0,3,1,2)).to(DEVICE)
        logits.append(m(t).cpu().numpy())
Lva=np.concatenate(logits)

def nll(T):
    lo=torch.from_numpy(Lva/float(T)); yy=torch.from_numpy(yva).long()
    return float(nn.functional.cross_entropy(lo,yy))
Ts=np.linspace(0.5,3.0,251); T=float(Ts[np.argmin([nll(t) for t in Ts])])
print("fitted temperature", round(T,3), "val NLL", round(nll(T),4))

# test logits from probabilities
logp=np.log(np.clip(prob,1e-12,1)); logits_test=logp  # softmax(log p / T) == normalised p^(1/T)
def softmax(z):
    z=z-z.max(1,keepdims=True); e=np.exp(z); return e/e.sum(1,keepdims=True)
prob_T=softmax(logits_test/T)

res=dict(temperature=T, ece_before=ece(prob,y), ece_after=ece(prob_T,y),
         brier_before=brier(prob,y), brier_after=brier(prob_T,y),
         mean_confidence=float(prob.max(1).mean()), accuracy=float((p==y).mean()))
json.dump(res,open(OUT/"calibration.json","w"),indent=2)
print(json.dumps(res,indent=1))

def reliability(prob_,y,n_bins=10):
    conf=prob_.max(1); pred=prob_.argmax(1); acc=(pred==y).astype(float)
    bins=np.linspace(0,1,n_bins+1); xs=[]; ys=[]; ns=[]
    for i in range(n_bins):
        m=(conf>bins[i])&(conf<=bins[i+1])
        if m.sum()>0:
            xs.append(conf[m].mean()); ys.append(acc[m].mean()); ns.append(m.sum())
    return np.array(xs),np.array(ys),np.array(ns)

fig,ax=plt.subplots(1,2,figsize=(7.4,3.0))
x1,y1,_=reliability(prob,y); x2,y2,_=reliability(prob_T,y)
ax[0].plot([0,1],[0,1],"k--",lw=1,label="Perfect calibration")
ax[0].plot(x1,y1,"o-",lw=1.4,ms=4,label=f"Uncalibrated (ECE={res['ece_before']:.3f})")
ax[0].plot(x2,y2,"s-",lw=1.4,ms=4,label=f"Temperature scaling (ECE={res['ece_after']:.3f})")
ax[0].set_xlabel("Mean predicted confidence"); ax[0].set_ylabel("Observed accuracy")
ax[0].legend(fontsize=6.5,loc="upper left"); ax[0].set_xlim(0,1); ax[0].set_ylim(0,1)
ax[1].hist(prob.max(1),bins=20,color="#777777",edgecolor="black",lw=0.4)
ax[1].set_xlabel("Predicted confidence"); ax[1].set_ylabel("Number of radiographs")
plt.tight_layout()
for e in ("png","pdf"): fig.savefig(FIG/f"figure5_calibration.{e}",dpi=600,bbox_inches="tight",facecolor="white")
print("figure saved")
