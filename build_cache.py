"""Cache the CLAHE-preprocessed radiographs as uint8 arrays to speed up training."""
import numpy as np
from pathlib import Path
import cv2
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/code2/knee-osteoarthritis-dataset-with-severity"
CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)


def prep(p):
    img = np.array(Image.open(p).convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    sh = np.clip(gray.astype(np.float64) - 0.5 * lap, 0, 255).astype(np.uint8)
    hp = np.clip(cv2.filter2D(sh, -1, np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])), 0, 255).astype(np.uint8)
    sm = cv2.GaussianBlur(hp, (3, 3), 0)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    out = clahe.apply(sm)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2RGB)


for split in ["train", "val", "test"]:
    files, labels = [], []
    for c in range(5):
        for p in sorted((DATA / split / str(c)).glob("*.png")):
            files.append(p); labels.append(c)
    arr = np.zeros((len(files), 224, 224, 3), dtype=np.uint8)
    for i, p in enumerate(files):
        arr[i] = prep(p)
        if i % 1000 == 0:
            print(split, i, flush=True)
    np.save(CACHE / f"{split}.npy", arr)
    np.save(CACHE / f"{split}_labels.npy", np.array(labels))
    with open(CACHE / f"{split}_files.txt", "w") as f:
        for p in files:
            f.write(str(p.relative_to(DATA)) + "\n")
    print("saved", split, arr.shape, flush=True)
