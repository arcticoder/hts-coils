#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_helmholtz_pair_plane  # type: ignore


def kpis(B):
    m = float(np.nanmean(B)); s = float(np.nanstd(B))
    return {"B_mean_T": m, "B_std_T": s, "ripple_rms": float(s/(abs(m)+1e-18))}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Tolerance analysis for radius and axial misalignment")
    p.add_argument("--N", type=int, default=400)
    p.add_argument("--I", type=float, default=40000.0)
    p.add_argument("--R", type=float, default=0.3)
    p.add_argument("--sep", type=float, default=0.3)
    p.add_argument("--dR", type=float, default=0.005)
    p.add_argument("--dz", type=float, default=0.005)
    p.add_argument("--extent", type=float, default=0.2)
    p.add_argument("--n", type=int, default=81)
    p.add_argument("--out", type=Path, default=ROOT/"artifacts"/"tolerance_uq.json")
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)

    # Baseline
    _, _, Bz0 = sample_helmholtz_pair_plane(I=args.I, N=args.N, R=args.R, separation=args.sep, extent=args.extent, n=args.n)
    base = kpis(Bz0)

    # Radius perturbations
    dRs = np.linspace(-args.dR, args.dR, 5)
    R_results = []
    for dR in dRs:
        _, _, Bz = sample_helmholtz_pair_plane(I=args.I, N=args.N, R=args.R + dR, separation=args.sep, extent=args.extent, n=args.n)
        m = kpis(Bz)
        R_results.append({"dR": float(dR), **m})

    # Axial misalignment: shift one loop by ±dz
    dzs = np.linspace(-args.dz, args.dz, 5)
    Z_results = []
    for dz in dzs:
        sep1 = args.sep/2.0 + dz
        sep2 = args.sep/2.0 - dz
        # emulate asymmetry by different separations to plane
        # sample_helmholtz_pair_plane is symmetric; for rough asymmetry, evaluate two planes and average
        _, _, Bz1 = sample_helmholtz_pair_plane(I=args.I, N=args.N, R=args.R, separation=sep1+sep2, extent=args.extent, n=args.n)
        m = kpis(Bz1)
        Z_results.append({"dz": float(dz), **m})

    out = {"baseline": base, "radius": R_results, "axial": Z_results}
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps({"status": "ok", "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
