#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import csv
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_circular_coil_plane, sample_helmholtz_pair_plane, sample_stack_plane  # type: ignore


def kpis(B):
    m = float(np.nanmean(B)); s = float(np.nanstd(B))
    return {"B_mean_T": m, "B_std_T": s, "ripple_rms": float(s/(abs(m)+1e-18))}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Sweep (N,I,R) and geometries; emit candidates CSV and top-k JSON")
    p.add_argument("--geom", choices=["single","helmholtz","stack"], default="single")
    p.add_argument("--N", nargs="*", type=int, default=[50,100,150,200])
    p.add_argument("--I", nargs="*", type=float, default=[2000,5000,10000,15000])
    p.add_argument("--R", nargs="*", type=float, default=[0.3,0.5,1.0])
    p.add_argument("--extent", type=float, default=0.2)
    p.add_argument("--n", type=int, default=81)
    p.add_argument("--sep", type=float, default=None, help="Helmholtz separation (default R)")
    p.add_argument("--layers", type=int, default=3)
    p.add_argument("--dz", type=float, default=0.2)
    p.add_argument("--out", type=Path, default=ROOT/"artifacts"/"sweep_results.csv")
    p.add_argument("--topk", type=int, default=10)
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)
    rows = []
    for N in args.N:
        for I in args.I:
            for R in args.R:
                if args.geom == "single":
                    _, _, Bz = sample_circular_coil_plane(I=I, N=N, R=R, extent=args.extent, n=args.n)
                elif args.geom == "helmholtz":
                    _, _, Bz = sample_helmholtz_pair_plane(I=I, N=N, R=R, separation=args.sep or R, extent=args.extent, n=args.n)
                else:
                    _, _, Bz = sample_stack_plane(I=I, N=N, R=R, layers=args.layers, axial_spacing=args.dz, extent=args.extent, n=args.n)
                m = kpis(Bz)
                rows.append({"geom": args.geom, "N": N, "I": I, "R": R, **m})

    # Write CSV
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # Select top-k meeting B>=5T, ripple<=1%
    candidates = [r for r in rows if r["B_mean_T"] >= 5.0 and r["ripple_rms"] <= 0.01]
    candidates.sort(key=lambda r: (r["ripple_rms"], -r["B_mean_T"]))
    topk = candidates[:args.topk]
    (ROOT/"artifacts"/"sweep_topk.json").write_text(json.dumps(topk, indent=2))
    print(json.dumps({"total": len(rows), "candidates": len(candidates), "topk": len(topk)}, indent=2))


if __name__ == "__main__":
    main()
