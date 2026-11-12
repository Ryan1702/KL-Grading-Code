"""Standalone evaluation of the best image-only checkpoint (no worker processes)."""
import json
import os
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tv_models
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
OUT = ROOT / os.environ.get("IO_OUT", "run_fast")
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

x = np.load(CACHE / "test.npy", mmap_mode="r")
y = np.load(CACHE / "test_labels.npy")

m = tv_models.resnet50(weights=None)
m.fc = nn.Linear(m.fc.in_features, 5)
m.load_state_dict(torch.load(OUT / "best_image_only.pth", map_location="cpu"))
m.to(DEVICE).eval()

preds, probs = [], []
BS = 32
with torch.no_grad():
    for i in range(0, len(y), BS):
        batch = np.array(x[i:i + BS]).astype(np.float32) / 255.0
        batch = (batch - MEAN) / STD
        t = torch.from_numpy(batch.transpose(0, 3, 1, 2)).to(DEVICE)
        p = torch.softmax(m(t), dim=1)
        probs.append(p.cpu().numpy()); preds.append(p.argmax(1).cpu().numpy())

p = np.concatenate(preds); pr = np.concatenate(probs)
aucs = [roc_auc_score((y == i).astype(int), pr[:, i]) for i in range(5)]
res = dict(n=len(y), correct=int((y == p).sum()), accuracy=float(accuracy_score(y, p)),
           macro_f1=float(f1_score(y, p, average="macro")),
           macro_precision=float(precision_score(y, p, average="macro")),
           macro_recall=float(recall_score(y, p, average="macro")),
           kappa_quadratic=float(cohen_kappa_score(y, p, weights="quadratic")),
           per_class={i: dict(recall=float(recall_score(y, p, labels=[i], average="macro")),
                              precision=float(precision_score(y, p, labels=[i], average="macro")),
                              f1=float(f1_score(y, p, labels=[i], average="macro")),
                              auc=float(aucs[i])) for i in range(5)},
           macro_auc=float(np.mean(aucs)), confusion=confusion_matrix(y, p).tolist())
(OUT / "image_only_results.json").write_text(json.dumps(res, indent=2))
np.savez(OUT / "image_only_preds.npz", y=y, pred=p, prob=pr)
print(json.dumps({k: v for k, v in res.items() if k not in ("per_class", "confusion")}, indent=1))
print(confusion_matrix(y, p))
