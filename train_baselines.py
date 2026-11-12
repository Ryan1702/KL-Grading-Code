"""Train ResNet-18, DenseNet-121 and ConvNeXt-Tiny under the same protocol as the main model."""
import json, time
from collections import Counter
from pathlib import Path
import cv2, numpy as np, torch, torch.nn as nn, torchvision.models as tv
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)

ROOT=Path(__file__).resolve().parent; CACHE=ROOT/"cache"; OUT=ROOT/"baselines"; OUT.mkdir(exist_ok=True)
DEVICE=torch.device("mps" if torch.backends.mps.is_available() else "cpu")
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)
LOG=open(OUT/"train_log.txt","w")
def log(*a):
    m=" ".join(map(str,a)); print(m,flush=True); LOG.write(m+"\n"); LOG.flush()

class C:
    def __init__(s,sp,tr):
        s.x=np.load(CACHE/f"{sp}.npy",mmap_mode="r"); s.y=np.load(CACHE/f"{sp}_labels.npy"); s.tr=tr
    def __len__(s): return len(s.y)
    def __getitem__(s,i):
        img=np.array(s.x[i])
        if s.tr:
            if np.random.rand()<0.5: img=img[:,::-1]
            if np.random.rand()<0.5:
                m=cv2.getRotationMatrix2D((112,112),np.random.uniform(-15,15),1.0)
                img=cv2.warpAffine(img,m,(224,224),borderMode=cv2.BORDER_REFLECT_101)
        return torch.from_numpy(((img.astype(np.float32)/255.0-MEAN)/STD).transpose(2,0,1)), int(s.y[i])

tr,va,te=C("train",True),C("val",False),C("test",False)
cnt=Counter(int(v) for v in tr.y); w=np.array([len(tr)/(5*cnt[int(c)]) for c in tr.y]); w=w/w.sum()

def build(name):
    if name=="resnet18":
        m=tv.resnet18(weights="DEFAULT"); m.fc=nn.Linear(m.fc.in_features,5); return m
    if name=="densenet121":
        m=tv.densenet121(weights="DEFAULT"); m.classifier=nn.Linear(m.classifier.in_features,5); return m
    if name=="resnet34":
        m=tv.resnet34(weights="DEFAULT"); m.fc=nn.Linear(m.fc.in_features,5); return m
    if name=="mobilenet_v2":
        m=tv.mobilenet_v2(weights="DEFAULT"); m.classifier[1]=nn.Linear(m.classifier[1].in_features,5); return m

def evaluate(ds, bs=64):
    m.eval(); pr=[]; prob=[]
    with torch.no_grad():
        for k in range(0,len(ds),bs):
            xs=torch.stack([ds[i][0] for i in range(k,min(k+bs,len(ds)))]).to(DEVICE)
            o=m(xs); prob.append(torch.softmax(o,1).cpu().numpy()); pr.append(o.argmax(1).cpu().numpy())
    return np.concatenate(pr), np.concatenate(prob)

results={}
for name in ["resnet34","mobilenet_v2"]:
    torch.manual_seed(42); np.random.seed(42)
    m=build(name).to(DEVICE)
    opt=torch.optim.AdamW(m.parameters(),lr=1e-4,weight_decay=0.01); lf=nn.CrossEntropyLoss()
    best=-1; bad=0; stop="max_epochs"; last=0; t0=time.time()
    log(f"=== {name} start ===")
    for ep in range(1,31):
        if ep==5:
            for g in opt.param_groups: g["lr"]=5e-5
        m.train(); tl=0; n=0
        idx=np.random.choice(len(tr),len(tr),replace=True,p=w)
        for k in range(0,len(idx),32):
            ch=idx[k:k+32]
            xs=torch.stack([tr[i][0] for i in ch]).to(DEVICE); ys=torch.tensor([tr[i][1] for i in ch]).to(DEVICE)
            opt.zero_grad(); loss=lf(m(xs),ys); loss.backward(); opt.step(); tl+=loss.item()*len(ch); n+=len(ch)
        p,_=evaluate(va); acc=accuracy_score(va.y,p); last=ep
        log(f"{name} epoch {ep} train_loss {tl/n:.4f} val_acc {acc:.4f} t {time.time()-t0:.0f}s")
        if acc>best+0.001:
            best=acc; bad=0; torch.save(m.state_dict(),OUT/f"{name}.pth"); log(f"  saved {best:.4f}")
        else:
            bad+=1
            if bad>=7: stop="early_stopping"; log(f"  early stop at {ep}"); break
        if time.time()-t0>3000: stop="time_cap"; log("  time cap"); break
        torch.mps.empty_cache()
    m.load_state_dict(torch.load(OUT/f"{name}.pth",map_location="cpu")); m.to(DEVICE)
    p,prob=evaluate(te); y=te.y
    aucs=[roc_auc_score((y==i).astype(int),prob[:,i]) for i in range(5)]
    results[name]=dict(n=len(y),accuracy=float(accuracy_score(y,p)),macro_f1=float(f1_score(y,p,average="macro")),
        macro_precision=float(precision_score(y,p,average="macro")),macro_recall=float(recall_score(y,p,average="macro")),
        kappa_quadratic=float(cohen_kappa_score(y,p,weights="quadratic")),macro_auc=float(np.mean(aucs)),
        per_class={str(i):dict(recall=float(recall_score(y,p,labels=[i],average="macro")),
                               precision=float(precision_score(y,p,labels=[i],average="macro")),
                               auc=float(aucs[i])) for i in range(5)},
        confusion=confusion_matrix(y,p).tolist(),best_val=float(best),best_epoch=int(last),stop=stop)
    json.dump(results,open(OUT/"baselines.json","w"),indent=2)
    log(f"{name}: acc {results[name]['accuracy']:.4f} f1 {results[name]['macro_f1']:.4f} qwk {results[name]['kappa_quadratic']:.4f} auc {results[name]['macro_auc']:.4f} stop {stop} ep {last}")
log("ALL DONE")
