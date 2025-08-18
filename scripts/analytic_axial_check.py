#!/usr/bin/env python3
from pathlib import Path
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import hts_coil_field, mu_0  # type: ignore


def analytic_center_field(N: int, I: float, R: float) -> float:
    return mu_0 * N * I / (2.0 * R)


def main() -> None:
    N, I, R = 100, 5000.0, 1.0
    Bz_numeric = hts_coil_field(np.array([0.0, 0.0, 0.0]), I=I, N=N, R=R)[2]
    Bz_analytic = analytic_center_field(N, I, R)
    rel_err = abs(Bz_numeric - Bz_analytic) / (abs(Bz_analytic) + 1e-18)
    out = {
        "numeric_T": float(Bz_numeric),
        "analytic_T": float(Bz_analytic),
        "relative_error": float(rel_err),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
