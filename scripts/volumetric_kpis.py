#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_plane_from_loops, sample_volume_from_loops, smear_loop_average  # type: ignore


def volumetric_kpis(Bmag: np.ndarray) -> dict:
    mean = float(np.nanmean(Bmag))
    std = float(np.nanstd(Bmag))
    ripple = float(std/(abs(mean)+1e-18))
    return {"B_mean_T": mean, "B_std_T": std, "ripple_rms": ripple}


def main():
    import argparse
    p = argparse.ArgumentParser(description="Compute volumetric KPIs and optional smear model")
    p.add_argument("--I", type=float, default=5000.0)
    p.add_argument("--N", type=int, default=100)
    p.add_argument("--R", type=float, default=1.0)
    p.add_argument("--width", type=float, default=0.0)
    p.add_argument("--thickness", type=float, default=0.0)
    p.add_argument("--extent", type=float, default=0.2)
    p.add_argument("--n", type=int, default=41)
    p.add_argument("--z_extent", type=float, default=0.2)
    p.add_argument("--nz", type=int, default=21)
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)
    loops = smear_loop_average(I=args.I, N=args.N, R=args.R, width=args.width, thickness=args.thickness)
    X,Y,Z,Bmag = sample_volume_from_loops(loops, extent=args.extent, n=args.n, z_extent=args.z_extent, nz=args.nz)
    kpi = volumetric_kpis(Bmag)
    out = {"kpis": kpi, "assumptions": vars(args)}
    (ROOT/"artifacts"/"volumetric_kpis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
