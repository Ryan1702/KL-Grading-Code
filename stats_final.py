"""Final statistics: identifier-level bootstrap (main model and paired differences),
cluster-level sign-flip permutation test, and Holm adjustment."""
import json, re
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score, roc_auc_score

ROOT = Path(__file__).resolve().parent
FM, BL = ROOT / "final_model", ROOT / "baselines"
files = [l.strip() for l in open(ROOT / "cache" / "test_files.txt")]
pids = np.array([re.match(r"(\d+)", Path(f).name).group(1) for f in files])
ug = np.unique(pids); idx = {g: np.where(pids == g)[0] for g in ug}

z = np.load(FM / "preds.npz"); y = z["y"]
models = {"ResNet-50": (z["pred"], z["prob"])}
for name, label in [("resnet18", "ResNet-18"), ("resnet34", "ResNet-34"), ("mobilenet_v2", "MobileNetV2")]:
    d = np.load(BL / f"{name}_preds.npz"); models[label] = (d["pred"], d["prob"])

def metrics(yy, p, pr):
    return dict(accuracy=accuracy_score(yy, p), macro_f1=f1_score(yy, p, average="macro"),
                qwk=cohen_kappa_score(yy, p, weights="quadratic"),
                macro_auc=roc_auc_score(yy, pr, multi_class="ovr", average="macro"))

B, SEED = 5000, 2026
main_p, main_pr = models["ResNet-50"]
rng = np.random.default_rng(SEED)
boot = {k: [] for k in ["accuracy", "macro_f1", "qwk", "macro_auc"]}
diffs = {lab: {k: [] for k in boot} for lab in models if lab != "ResNet-50"}
for _ in range(B):
    pick = rng.choice(ug, len(ug), replace=True)
    ii = np.concatenate([idx[g] for g in pick]); yy = y[ii]
    m = metrics(yy, main_p[ii], main_pr[ii])
    for k in boot: boot[k].append(m[k])
    for lab, (p, pr) in models.items():
        if lab == "ResNet-50": continue
        b = metrics(yy, p[ii], pr[ii])
        for k in boot: diffs[lab][k].append(m[k] - b[k])

ci = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in boot.items()}
diff_out = {}
for lab, dv in diffs.items():
    diff_out[lab] = dict(
        mean={k: float(np.mean(v)) for k, v in dv.items()},
        ci={k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in dv.items()})

def cluster_perm(p_base, n_perm=10000, seed=7):
    a = (main_p == y).astype(float); b = (p_base == y).astype(float)
    dd = np.array([(a[ii] - b[ii]).mean() for ii in idx.values()])
    obs = dd.mean(); r = np.random.default_rng(seed); cnt = 0
    for _ in range(n_perm):
        s = r.choice([-1.0, 1.0], len(dd))
        cnt += abs((dd * s).mean()) >= abs(obs)
    return float(obs), float((cnt + 1) / (n_perm + 1))

perm = {lab: cluster_perm(p) for lab, (p, pr) in models.items() if lab != "ResNet-50"}
order = sorted(perm, key=lambda k: perm[k][1])
m_adj, running = {}, 0.0
for rank, lab in enumerate(order):
    val = min(1.0, (len(order) - rank) * perm[lab][1])
    running = max(running, val); m_adj[lab] = running

out = dict(bootstrap=dict(n_resamples=B, seed=SEED, unit="file identifier", interval="percentile",
                          point=metrics(y, main_p, main_pr), ci=ci),
           paired=dict(n_resamples=B, seed=SEED, differences=diff_out),
           permutation=dict(n_permutations=10000, seed=7,
                            raw={k: v[1] for k, v in perm.items()}, holm=m_adj))
json.dump(out, open(FM / "stats_final.json", "w"), indent=2)
print("main CI:", {k: [round(100*x,1) if k in ("accuracy","macro_auc") else round(x,3) for x in v] for k, v in ci.items()})
for lab in diff_out:
    d = diff_out[lab]
    print(f"{lab}: dAcc {100*d['mean']['accuracy']:+.1f} [{100*d['ci']['accuracy'][0]:+.1f},{100*d['ci']['accuracy'][1]:+.1f}] "
          f"dAUC {d['mean']['macro_auc']:+.3f} [{d['ci']['macro_auc'][0]:+.3f},{d['ci']['macro_auc'][1]:+.3f}] "
          f"perm p={perm[lab][1]:.3f} holm={m_adj[lab]:.3f}")
