# Automated Kellgren–Lawrence grading of knee osteoarthritis (image-only)

Code, configuration and reported results for the manuscript

> **Automated Kellgren–Lawrence Grading of Knee Osteoarthritis from Plain Radiographs:
> Development and Internal Validation with Grad-CAM Explanations**

This repository reproduces every number, table and figure of the manuscript from the
public dataset.

## Contents

| Path | Content |
|---|---|
| `build_cache.py` | CLAHE preprocessing cache for the three partitions |
| `train_image_only_fast.py` | ResNet-50 training (seed 42, batch 32, AdamW, early stopping) |
| `run_to_earlystop.py` | continuation until the stopping criterion (epoch 18; best epoch 11) |
| `eval_standalone.py` | test-set predictions of the retained checkpoint |
| `quick_analysis.py` | metrics, Wilson intervals, identifier-level cluster bootstrap |
| `train_baselines.py`, `baseline_preds.py` | ResNet-18, ResNet-34 and MobileNetV2 under the same protocol |
| `stats_final.py` | 5,000-resample cluster bootstrap and cluster-level sign-flip permutation test |
| `calibration.py` | expected calibration error, Brier score, temperature scaling |
| `make_figures.py`, `make_gradcam_io.py`, `make_flowchart.py` | Figures 1–5 |
| `results/` | `analysis.json`, `stats_final.json`, `calibration.json` and the reported figures |

## Reproducing the results

```bash
python -m pip install -r requirements.txt
# download the dataset (doi:10.17632/56rmx5bjcr.1) and extract it to
# data/code2/knee-osteoarthritis-dataset-with-severity/{train,val,test}/{0-4}/*.png
bash run_all.sh
```

Runtime on a single Apple M1 GPU is approximately 2.5 hours (training dominates).
Random seeds: 42 (training), 2026 (bootstrap), 7 (permutation test).
The test partition is evaluated once, after all training and model selection.

## Reported results

| Metric | Value |
|---|---|
| Accuracy (1,656 test radiographs) | 63.5% (1,051/1,656) |
| Wilson 95% CI | 61.1–65.8% |
| Cluster bootstrap 95% CI | 60.9–65.9% |
| Macro F1 | 0.649 (0.620–0.674) |
| Quadratic-weighted κ | 0.792 (0.768–0.814) |
| Macro AUC | 0.876 (0.865–0.887) |
| Calibration (ECE) | 0.162 → 0.026 after temperature scaling |

## Data

The radiographs are not redistributed here. They are publicly available as the
Knee Osteoarthritis Severity Grading Dataset (Mendeley Data,
doi:10.17632/56rmx5bjcr.1, version 1). The partitions distributed with the release
are used without modification. `Table_S1_partitions.csv` in the supplementary
material lists the identifier, laterality, split and KL grade of every radiograph.

## Environment

Python 3.14.2 · PyTorch 2.15.0 · torchvision 0.29.2 · NumPy 2.5.4 · OpenCV 5.0.0 ·
Pillow 13.0.0 · scikit-learn 1.9.1 · SciPy 1.18.1 · Matplotlib 3.11.2.
Training used a single Apple M1 GPU through Metal Performance Shaders; no CUDA
device was used.

## License

Code released under the MIT License (see `LICENSE`). The dataset remains under
its own license.

## Citation

If you use this code, please cite the manuscript and the archived release:

> Wu Y. *Automated Kellgren–Lawrence grading of knee osteoarthritis: image-only pipeline*
> (v1.0.0). Zenodo; 2026.
> [doi:10.5281/zenodo.24178624](https://doi.org/10.5281/zenodo.24178624)
