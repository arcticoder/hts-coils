#!/usr/bin/env python3
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:  # pragma: no cover
    plt = None

# Ensure local src is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts import sample_circular_coil_plane  # type: ignore


ARTIFACTS = ROOT / "artifacts"
DATA = ROOT / "data"
ARTIFACTS.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)


def compute_ripple_kpis(B: np.ndarray) -> Dict[str, float]:
    mean = float(np.nanmean(B))
    std = float(np.nanstd(B))
    ripple_rms = float(std / (abs(mean) + 1e-18))
    return {"B_mean_T": mean, "B_std_T": std, "ripple_rms": ripple_rms}


def main() -> None:
    X, Y, Bz = sample_circular_coil_plane(I=5000.0, N=100, R=1.0, extent=0.2, n=81)
    kpi = compute_ripple_kpis(Bz)
    with open(ARTIFACTS / "field_uniformity_report.json", "w") as f:
        json.dump(kpi, f, indent=2)

    if plt is not None:
        # Centerline (x=0) plot
        mid = Bz.shape[1] // 2
        fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        ax[0].plot(Y[:, mid], Bz[:, mid])
        ax[0].set_title("Bz centerline (x=0)")
        ax[0].set_xlabel("y [m]")
        ax[0].set_ylabel("Bz [T]")
        ax[0].grid(True, alpha=0.3)

        # Ripple heatmap
        im = ax[1].imshow(Bz, extent=[X.min(), X.max(), Y.min(), Y.max()], origin="lower")
        ax[1].set_title("Bz plane (z=0)")
        ax[1].set_xlabel("x [m]")
        ax[1].set_ylabel("y [m]")
        fig.colorbar(im, ax=ax[1], shrink=0.9, label="Bz [T]")
        fig.tight_layout()
        fig.savefig(ARTIFACTS / "b_field_centerline.png", dpi=150)
        fig.savefig(ARTIFACTS / "b_field_ripple.png", dpi=150)
        plt.close(fig)

    # Basic feasibility report stub
    feas = {
        "B_mean_T": kpi["B_mean_T"],
        "ripple_rms": kpi["ripple_rms"],
        "gates": {
            "B_mean>=5T": kpi["B_mean_T"] >= 5.0,
            "ripple<=0.0001": kpi["ripple_rms"] <= 1e-4,
        },
    }
    with open(ROOT / "feasibility_gates_report.json", "w") as f:
        json.dump(feas, f, indent=2)


if __name__ == "__main__":
    main()
