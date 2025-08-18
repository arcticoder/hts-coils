#!/usr/bin/env python3
import os, sys, json
from pathlib import Path
import numpy as np
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hts import sample_circular_coil_plane  # type: ignore
ARTIFACTS = ROOT / "artifacts"; ARTIFACTS.mkdir(exist_ok=True)
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)

def kpis(B: np.ndarray):
    mean = float(np.nanmean(B)); std = float(np.nanstd(B)); ripple = float(std/ (abs(mean)+1e-18))
    return {"B_mean_T": mean, "B_std_T": std, "ripple_rms": ripple}

def main():
    X, Y, Bz = sample_circular_coil_plane(I=5000.0, N=100, R=1.0, extent=0.2, n=81)
    m = kpis(Bz)
    (ARTIFACTS / "field_uniformity_report.json").write_text(json.dumps(m, indent=2))
    if plt is not None:
        mid = Bz.shape[1]//2
        fig, ax = plt.subplots(1,2, figsize=(10,4))
        ax[0].plot(Y[:,mid], Bz[:,mid]); ax[0].set_title("Bz centerline (x=0)"); ax[0].grid(True, alpha=0.3)
        im = ax[1].imshow(Bz, extent=[X.min(), X.max(), Y.min(), Y.max()], origin="lower"); fig.colorbar(im, ax=ax[1])
        fig.tight_layout(); fig.savefig(ARTIFACTS/"b_field_centerline.png", dpi=150); fig.savefig(ARTIFACTS/"b_field_ripple.png", dpi=150); plt.close(fig)
    feas = {"B_mean_T": m["B_mean_T"], "ripple_rms": m["ripple_rms"], "gates": {"B_mean>=5T": m["B_mean_T"]>=5.0, "ripple<=0.01": m["ripple_rms"]<=0.01}}
    (ROOT/"feasibility_gates_report.json").write_text(json.dumps(feas, indent=2))
if __name__ == "__main__":
    main()
