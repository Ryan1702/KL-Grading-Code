"""Continue image-only training until early stopping (patience 7) or 30 total epochs."""
import json, time
from collections import Counter
from pathlib import Path
import cv2, numpy as np, torch, torch.nn as nn, torchvision.models as tv_models
from sklearn.metrics import accuracy_score
ROOT=Path(__file__).resolve().parent; CACHE=ROOT/"cache"; OUT=ROOT/"final_model"
DEVICE=torch.device("mps" if torch.backends.mps.is_available() else "cpu")
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)
LOG=open(OUT/"finish_log.txt","w")
def log(*a):
    m=" ".join(map(str,a)); print(m,flush=True); LOG.write(m+"\n"); LOG.flush()
class C:
    def __init__(s,sp,tr): s.x=np.load(CACHE/f"{sp}.npy",mmap_mode="r"); s.y=np.load(CACHE/f"{sp}_labels.npy"); s.tr=tr
    def __len__(s): return len(s.y)
    def __getitem__(s,i):
        img=np.array(s.x[i])
        if s.tr:
            if np.random.rand()<0.5: img=img[:,::-1]
            if np.random.rand()<0.5:
                m=cv2.getRotationMatrix2D((112,112),np.random.uniform(-15,15),1.0)
                img=cv2.warpAffine(img,m,(224,224),borderMode=cv2.BORDER_REFLECT_101)
        return torch.from_numpy(((img.astype(np.float32)/255.0-MEAN)/STD).transpose(2,0,1)), int(s.y[i])
torch.manual_seed(123); np.random.seed(123)
tr,va=C("train",True),C("val",False)
cnt=Counter(int(v) for v in tr.y); w=np.array([len(tr)/(5*cnt[int(c)]) for c in tr.y]); w=w/w.sum()
m=tv_models.resnet50(weights=None); m.fc=nn.Linear(m.fc.in_features,5)
m.load_state_dict(torch.load(OUT/"best_image_only.pth",map_location="cpu")); m.to(DEVICE)
opt=torch.optim.AdamW(m.parameters(),lr=5e-5,weight_decay=0.01); lf=nn.CrossEntropyLoss()
def val():
    m.eval(); pr=[]
    with torch.no_grad():
        for k in range(0,len(va),64):
            xs=torch.stack([va[i][0] for i in range(k,min(k+64,len(va)))]).to(DEVICE)
            pr.append(m(xs).argmax(1).cpu().numpy())
    return accuracy_score(va.y,np.concatenate(pr))
best=val(); log("start val",round(best,4)); bad=0
for ep in range(10,31):
    m.train(); t0=time.time(); idx=np.random.choice(len(tr),len(tr),replace=True,p=w); n=0
    for k in range(0,len(idx),32):
        ch=idx[k:k+32]
        xs=torch.stack([tr[i][0] for i in ch]).to(DEVICE); ys=torch.tensor([tr[i][1] for i in ch]).to(DEVICE)
        opt.zero_grad(); loss=lf(m(xs),ys); loss.backward(); opt.step(); n+=len(ch)
    a=val(); log(f"epoch {ep} val {a:.4f} t {time.time()-t0:.0f}s")
    if a>best+0.001:
        best=a; bad=0; torch.save(m.state_dict(),OUT/"best_image_only.pth"); log("saved",round(a,4))
    else:
        bad+=1
        if bad>=7: log("early stop at epoch",ep); break
log("done best",round(best,4))
