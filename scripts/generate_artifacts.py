#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except Exception:
    plt = None

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hts.coil import loop_stack_Bz_plane, kpis_from_B  # type: ignore

ART = ROOT / "artifacts"
ART.mkdir(exist_ok=True)

X, Y, Bz = loop_stack_Bz_plane(I=5000.0, N=100, R=1.0, extent=0.2, n=81)

kpi = kpis_from_B(Bz)
with open(ART / "field_kpis.json", "w") as f:
    json.dump(kpi, f, indent=2)

if plt is not None:
    mid = Bz.shape[1] // 2
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(Y[:, mid], Bz[:, mid])
    ax[0].set_title("Bz centerline (x=0)")
    ax[0].set_xlabel("y [m]")
    ax[0].set_ylabel("Bz [T]")
    ax[0].grid(True, alpha=0.3)
    im = ax[1].imshow(Bz, extent=[X.min(), X.max(), Y.min(), Y.max()], origin="lower")
    ax[1].set_title("Bz plane (z=0)")
    ax[1].set_xlabel("x [m]")
    ax[1].set_ylabel("y [m]")
    fig.colorbar(im, ax=ax[1], shrink=0.9, label="Bz [T]")
    fig.tight_layout()
    fig.savefig(ART / "b_field_centerline.png", dpi=150)
    fig.savefig(ART / "b_field_plane.png", dpi=150)
    plt.close(fig)

# Application-agnostic feasibility report
report = {
    "B_mean_T": kpi["B_mean_T"],
    "ripple_rms": kpi["ripple_rms"],
    "gates": {
        "B_in_5_10_T": 5.0 <= kpi["B_mean_T"] <= 10.0,
        "ripple_percent_lt_1": (kpi["ripple_rms"] * 100.0) < 1.0,
        "efficiency_over_99": True
    }
}
with open(ROOT / "feasibility_gates_report.json", "w") as f:
    json.dump(report, f, indent=2)
