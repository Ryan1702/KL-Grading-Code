"""Regenerate Figure 1 (confusion matrix), Figure 3 (ROC) and Figure 2 (Grad-CAM) for the image-only model."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.preprocessing import label_binarize

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "final_model"
FIG = OUT / "figures"; FIG.mkdir(exist_ok=True)
z = np.load(OUT / "preds.npz")
y, p, prob = z["y"], z["pred"], z["prob"]
res = json.loads((OUT / "analysis.json").read_text())

cm = confusion_matrix(y, p).astype(float)
cmn = cm / cm.sum(1, keepdims=True)
plt.figure(figsize=(6.2, 5.2))
im = plt.imshow(cmn, cmap="viridis", vmin=0, vmax=1)
for i in range(5):
    for j in range(5):
        plt.text(j, i, f"{cmn[i,j]:.2f}", ha="center", va="center", fontsize=9,
                 color="white" if cmn[i, j] < 0.6 else "black")
plt.xticks(range(5), [f"KL {i}" for i in range(5)], fontsize=8)
plt.yticks(range(5), [f"KL {i}" for i in range(5)], fontsize=8)
plt.xlabel("Predicted KL grade", fontsize=9); plt.ylabel("Reference KL grade", fontsize=9)
plt.colorbar(im, fraction=0.046, pad=0.04, label="Proportion")
plt.tight_layout()
for ext in ["png", "pdf"]:
    plt.savefig(FIG / f"figure1_confusion.{ext}", dpi=600, bbox_inches="tight")
plt.close()

ybin = label_binarize(y, classes=list(range(5)))
plt.figure(figsize=(5.6, 5.0))
for i, c in enumerate(["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#e6b800"]):
    fpr, tpr, _ = roc_curve(ybin[:, i], prob[:, i])
    plt.plot(fpr, tpr, lw=1.8, color=c, label=f"KL {i} (AUC = {res['per_class'][str(i)]['auc']:.3f})")
plt.plot([0, 1], [0, 1], "k--", lw=1.2)
plt.xlim([0, 1]); plt.ylim([0, 1.02])
plt.xlabel("1 − specificity", fontsize=9); plt.ylabel("Sensitivity", fontsize=9)
plt.legend(loc="lower right", fontsize=7.5, frameon=True)
plt.tight_layout()
for ext in ["png", "pdf"]:
    plt.savefig(FIG / f"figure3_roc.{ext}", dpi=600, bbox_inches="tight")
plt.close()
print("figures 1 and 3 done", res["macro_auc"])
