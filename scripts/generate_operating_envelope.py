#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts import sample_circular_coil_plane  # type: ignore


def main() -> None:
    X, Y, Bz = sample_circular_coil_plane(I=5000.0, N=100, R=1.0, extent=0.2, n=81)
    mean = float(np.nanmean(Bz)); std = float(np.nanstd(Bz))
    env = {
        "B_mean_T": mean,
        "B_std_T": std,
        "ripple_rms": float(std/(abs(mean)+1e-18)),
        "assumptions": {
            "I_A": 5000.0,
            "N_turns": 100,
            "R_m": 1.0,
            "grid_extent_m": 0.2,
            "grid_points": 81,
            "T_K": 77.0,
            "Tc_K": 90.0,
        }
    }
    (ROOT / "artifacts").mkdir(exist_ok=True)
    (ROOT / "artifacts" / "operating_envelope.json").write_text(json.dumps(env, indent=2))
    print(json.dumps(env, indent=2))


if __name__ == "__main__":
    main()
