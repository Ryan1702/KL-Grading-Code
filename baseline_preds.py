"""Generate test-set predictions for the baseline checkpoints."""
import numpy as np, torch, torch.nn as nn, torchvision.models as tv
from pathlib import Path

ROOT=Path(__file__).resolve().parent; CACHE=ROOT/"cache"; BL=ROOT/"baselines"
DEVICE=torch.device("mps" if torch.backends.mps.is_available() else "cpu")
MEAN=np.array([0.485,0.456,0.406],np.float32); STD=np.array([0.229,0.224,0.225],np.float32)

def build(name):
    if name=="resnet18":
        m=tv.resnet18(weights=None); m.fc=nn.Linear(m.fc.in_features,5); return m
    if name=="resnet34":
        m=tv.resnet34(weights=None); m.fc=nn.Linear(m.fc.in_features,5); return m
    if name=="mobilenet_v2":
        m=tv.mobilenet_v2(weights=None); m.classifier[1]=nn.Linear(m.classifier[1].in_features,5); return m

X=np.load(CACHE/"test.npy",mmap_mode="r"); y=np.load(CACHE/"test_labels.npy")
for name in ["resnet18","resnet34","mobilenet_v2"]:
    m=build(name); m.load_state_dict(torch.load(BL/f"{name}.pth",map_location="cpu")); m.to(DEVICE).eval()
    pred=[]; prob=[]
    with torch.no_grad():
        for k in range(0,len(y),64):
            xs=np.array(X[k:k+64]).astype(np.float32)/255.0
            xs=(xs-MEAN)/STD
            t=torch.from_numpy(xs.transpose(0,3,1,2)).to(DEVICE)
            o=m(t); prob.append(torch.softmax(o,1).cpu().numpy()); pred.append(o.argmax(1).cpu().numpy())
    np.savez(BL/f"{name}_preds.npz", y=y, pred=np.concatenate(pred), prob=np.concatenate(prob))
    print(name, "done")
