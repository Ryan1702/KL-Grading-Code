"""Fast image-only baseline using cached CLAHE-preprocessed arrays.

Protocol (identical to the multimodal training as far as the shared code defines it):
  ResNet-50 (ImageNet) fully fine-tuned, AdamW 1e-4 / wd 0.01, batch 32,
  max 30 epochs, early stopping on validation accuracy (patience 7, min_delta 0.001),
  WeightedRandomSampler, seed 42, horizontal flip + rotation +/-15 deg.
"""
import json
import os
import time
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tv_models
from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
OUT = ROOT / os.environ.get("IO_OUT", "imageonly_fast")
OUT.mkdir(exist_ok=True)
LOG = open(OUT / "train_log.txt", "w")


def log(*a):
    msg = " ".join(str(x) for x in a)
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()


torch.manual_seed(42)
np.random.seed(42)
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
EPOCHS, BS, LR, WD = 30, 32, 1e-4, 0.01
PATIENCE, MIN_DELTA = 7, 0.001
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class Cached(Dataset):
    def __init__(self, split, train):
        self.x = np.load(CACHE / f"{split}.npy", mmap_mode="r")
        self.y = np.load(CACHE / f"{split}_labels.npy")
        self.train = train

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        img = np.array(self.x[i])
        if self.train:
            if np.random.rand() < 0.5:
                img = img[:, ::-1]
            if np.random.rand() < 0.5:
                ang = np.random.uniform(-15, 15)
                m = cv2.getRotationMatrix2D((112, 112), ang, 1.0)
                img = cv2.warpAffine(img, m, (224, 224), flags=cv2.INTER_LINEAR,
                                     borderMode=cv2.BORDER_REFLECT_101)
        x = (img.astype(np.float32) / 255.0 - MEAN) / STD
        return torch.from_numpy(x.transpose(2, 0, 1)), int(self.y[i])


def build():
    m = tv_models.resnet50(weights="DEFAULT")
    m.fc = nn.Linear(m.fc.in_features, 5)
    return m


@torch.no_grad()
def evaluate(model, loader):
    model.eval()
    ys, ps, pr = [], [], []
    for x, y in loader:
        o = model(x.to(DEVICE))
        p = torch.softmax(o, dim=1)
        pr.append(p.cpu().numpy()); ps.append(p.argmax(1).cpu().numpy()); ys.append(np.array(y))
    return (np.concatenate(ys), np.concatenate(ps), np.concatenate(pr))


def main():
    tr, va, te = Cached("train", True), Cached("val", False), Cached("test", False)
    log(f"train {len(tr)} val {len(va)} test {len(te)} device {DEVICE}")
    cnt = Counter(int(v) for v in tr.y)
    w = {c: len(tr) / (5 * n) for c, n in cnt.items()}
    sampler = WeightedRandomSampler([w[int(v)] for v in tr.y], len(tr), replacement=True)
    tl = DataLoader(tr, batch_size=BS, sampler=sampler, num_workers=4, persistent_workers=True)
    vl = DataLoader(va, batch_size=BS, shuffle=False, num_workers=4, persistent_workers=True)
    tel = DataLoader(te, batch_size=BS, shuffle=False, num_workers=4, persistent_workers=True)

    model = build().to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WD)
    lossf = nn.CrossEntropyLoss()
    best, best_ep, bad = -1.0, 0, 0

    for ep in range(1, EPOCHS + 1):
        model.train(); t0 = time.time(); tot = 0
        for step, (x, y) in enumerate(tl, 1):
            x, y = x.to(DEVICE), y.to(DEVICE)
            opt.zero_grad()
            loss = lossf(model(x), y)
            loss.backward(); opt.step(); tot += x.size(0)
            if step % 40 == 0:
                log(f"  ep{ep:02d} {step}/{len(tl)} loss {loss.item():.4f} ({time.time()-t0:.0f}s)")
        yv, pv, _ = evaluate(model, vl)
        acc = accuracy_score(yv, pv)
        log(f"epoch {ep:02d} val_acc {acc:.4f} {time.time()-t0:.0f}s")
        if acc > best + MIN_DELTA:
            best, best_ep, bad = acc, ep, 0
            torch.save(model.state_dict(), OUT / "best_image_only.pth")
            log(f"  saved best {best:.4f}")
        else:
            bad += 1
            if bad >= PATIENCE:
                log("early stop"); break

    log("best epoch", best_ep, "val acc", round(best, 4))
    model.load_state_dict(torch.load(OUT / "best_image_only.pth", map_location=DEVICE))
    y, p, pr = evaluate(model, tel)
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
               macro_auc=float(np.mean(aucs)), confusion=confusion_matrix(y, p).tolist(),
               best_epoch=best_ep, best_val_acc=float(best))
    (OUT / "image_only_results.json").write_text(json.dumps(res, indent=2))
    np.savez(OUT / "image_only_preds.npz", y=y, pred=p, prob=pr)
    log(json.dumps({k: v for k, v in res.items() if k not in ("per_class", "confusion")}, indent=1))
    log("confusion:\n" + str(confusion_matrix(y, p)))


if __name__ == "__main__":
    main()
