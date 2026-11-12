# -*- coding: utf-8 -*-
"""Study workflow figure for the manuscript."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "audit" / "final_model" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "serif"
plt.rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]

stages = [
    ("Dataset",
     "8,260 knee radiographs  ·  4,130 participants\n"
     "Knee Osteoarthritis Severity Grading Dataset (Mendeley Data)"),
    ("File identifier grouping",
     "Training 5,778  ·  Validation 826  ·  Test 1,656\n"
     "No identifier shared; both knees of an identifier kept together"),
    ("Image preprocessing and augmentation",
     "Unsharp masking, high-pass filter, Gaussian smoothing, CLAHE\n"
     "Horizontal flip and ±15° rotation during training only"),
    ("Network",
     "ImageNet ResNet-50  →  global average pooling (2,048)\n"
     "Fully connected layer  →  five KL classes"),
    ("Training",
     "AdamW 1e-4 → 5e-5, batch 32, weighted sampling\n"
     "Early stopping at epoch 18 (patience 7); best checkpoint epoch 11"),
    ("Evaluation on the held-out test set",
     "Accuracy, macro F1, quadratic-weighted κ, macro AUC (95% CI)\n"
     "Confusion matrix, ROC curves, Grad-CAM"),
]

n = len(stages)
fig_w, box_h, gap = 6.6, 0.62, 0.26
fig_h = n * box_h + (n - 1) * gap + 0.5
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.set_xlim(0, 1)
ax.set_ylim(0, fig_h)
ax.axis("off")

y = fig_h - 0.25
for i, (title, detail) in enumerate(stages):
    top = y
    y -= box_h
    box = FancyBboxPatch((0.03, y), 0.94, box_h,
                         boxstyle="round,pad=0.012,rounding_size=0.02",
                         linewidth=1.0, edgecolor="black",
                         facecolor="#f2f2f2" if i % 2 == 0 else "white")
    ax.add_patch(box)
    ax.text(0.5, y + box_h * 0.68, title, ha="center", va="center",
            fontsize=9.2, fontweight="bold")
    ax.text(0.5, y + box_h * 0.28, detail, ha="center", va="center", fontsize=7.6)
    if i < n - 1:
        ax.annotate("", xy=(0.5, y - gap + 0.02), xytext=(0.5, y - 0.005),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=1.1,
                                    shrinkA=0, shrinkB=0))
    y -= gap

for ext in ("png", "pdf"):
    fig.savefig(OUT / f"figure0_pipeline.{ext}", dpi=600, bbox_inches="tight", facecolor="white")
print("saved", OUT)
