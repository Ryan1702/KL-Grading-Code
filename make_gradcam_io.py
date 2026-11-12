"""Grad-CAM for the image-only ResNet-50 (5 cases, one per KL grade)."""
from pathlib import Path
import cv2, numpy as np, torch, torch.nn as nn, torchvision.models as tv_models
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / "cache"
OUT = ROOT / "final_model"; FIG = OUT / "figures"
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
MEAN = np.array([0.485,0.456,0.406], np.float32); STD = np.array([0.229,0.224,0.225], np.float32)
z = np.load(OUT / "preds.npz"); y, pred = z["y"], z["pred"]
files=[l.strip() for l in open(ROOT/"cache"/"test_files.txt")]
DATA=ROOT/"data/code2/knee-osteoarthritis-dataset-with-severity"

x = np.load(CACHE / "test.npy", mmap_mode="r")
m = tv_models.resnet50(weights=None); m.fc = nn.Linear(m.fc.in_features, 5)
m.load_state_dict(torch.load(OUT/"best_image_only.pth", map_location="cpu")); m.to(DEVICE).eval()

chosen = []
for c in range(5):
    idx = [i for i in range(len(y)) if y[i] == c and pred[i] == c]
    chosen.append(idx[0] if idx else [i for i in range(len(y)) if y[i] == c][0])

def cam_for(i, cls):
    feats, grads = [], []
    layer = m.layer4[-1]
    h1 = layer.register_forward_hook(lambda mod, inp, out: feats.append(out))
    h2 = layer.register_full_backward_hook(lambda mod, gi, go: grads.append(go[0]))
    img = np.array(x[i]).astype(np.float32) / 255.0
    t = torch.from_numpy(((img - MEAN) / STD).transpose(2, 0, 1)).unsqueeze(0).to(DEVICE).requires_grad_(True)
    out = m(t); m.zero_grad(); out[0, cls].backward(); h1.remove(); h2.remove()
    g = grads[0].detach().cpu().numpy().squeeze(); f = feats[0].detach().cpu().numpy().squeeze()
    w = g.mean(axis=(1, 2)); cam = np.maximum((w[:, None, None] * f).sum(0), 0)
    cam = cv2.resize(cam, (224, 224)); cam = (cam - cam.min()) / (cam.max() + 1e-8)
    from PIL import Image
    raw = np.array(Image.open(DATA/files[i]).convert("RGB").resize((224,224)))
    return cam, raw

fig = plt.figure(figsize=(6.6, 4.4))
gs = fig.add_gridspec(2, 6, wspace=0.02, hspace=0.03)
slots = [gs[0, 0:2], gs[0, 2:4], gs[0, 4:6], gs[1, 1:3], gs[1, 3:5]]
for k, (i, sl) in enumerate(zip(chosen, slots)):
    cam, raw = cam_for(i, int(pred[i]))
    heat = cv2.applyColorMap(np.uint8(255*cam), cv2.COLORMAP_JET); heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    over = cv2.addWeighted(raw, 0.5, heat, 0.5, 0)
    ax = fig.add_subplot(sl); ax.axis("off"); ax.imshow(over)
    ax.text(0.035, 0.955, f"KL {y[i]}", transform=ax.transAxes, fontsize=8.5, fontweight="bold",
            va="top", ha="left", color="white", bbox=dict(facecolor="black", alpha=0.55, pad=1.2, lw=0))
for ext in ["png", "pdf"]:
    fig.savefig(FIG / f"figure2_gradcam.{ext}", dpi=600, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"figure2_gradcam.{ext}", dpi=600, bbox_inches="tight", facecolor="white")
print("gradcam done", chosen)
