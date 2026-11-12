#!/usr/bin/env bash
set -e
python build_cache.py
python train_image_only_fast.py
python run_to_earlystop.py
python eval_standalone.py
python quick_analysis.py
python train_baselines.py
python baseline_preds.py
python stats_final.py
python calibration.py
python make_figures.py
python make_gradcam_io.py
python make_flowchart.py
echo "done: see final_model/ and baselines/"
