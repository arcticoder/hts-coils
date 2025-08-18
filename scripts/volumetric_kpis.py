#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_plane_from_loops, sample_volume_from_loops, smear_loop_average, stack_layers_loops  # type: ignore
from hts.config import load_config, cache_path_for  # type: ignore
from hts.metrics import stored_magnetic_energy_grid, efficiency_hts_approx  # type: ignore


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
    p.add_argument("--shape", choices=["rect","round"], default="rect")
    p.add_argument("--cs_radius", type=float, default=0.0)
    p.add_argument("--layers", type=int, default=1)
    p.add_argument("--delta_R", type=float, default=0.0, help="per-layer radius increment across stack")
    p.add_argument("--extent", type=float, default=0.2)
    p.add_argument("--n", type=int, default=41)
    p.add_argument("--z_extent", type=float, default=0.2)
    p.add_argument("--nz", type=int, default=21)
    p.add_argument("--uniformity_pct", type=float, default=1.0, help="Compute coverage fraction within ±pct of mean")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--R_circ", type=float, default=0.0, help="Optional residual circuit resistance (Ohm)")
    p.add_argument("--duration", type=float, default=1.0, help="Time window for efficiency loss calc (s)")
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)
    cli_overrides = vars(args)
    cfg, cfg_hash = load_config(args.config, cli_overrides)

    # Build loops: stack if layers>1 then smear each layer
    base_loops = stack_layers_loops(I=args.I, N=args.N, R=args.R, layers=args.layers, axial_spacing=args.thickness if args.layers>1 else 0.0, delta_R=args.delta_R)
    loops = []
    for (I0,N0,R0,z0) in base_loops:
        smeared = smear_loop_average(I=I0, N=N0, R=R0, width=args.width, thickness=args.thickness, shape=args.shape, cs_radius=args.cs_radius)
        # offset each smeared subloop by z0
        loops.extend([(Ii, Ni, Ri, z0 + zi) for (Ii,Ni,Ri,zi) in smeared])

    cache = cache_path_for(cfg_hash, f"volume-N{args.N}-I{args.I}-R{args.R}-n{args.n}-nz{args.nz}")
    if cache.exists():
        data = np.load(cache)
        X = data["X"]; Y = data["Y"]; Z = data["Z"]; Bmag = data["Bmag"]
    else:
        X,Y,Z,Bmag = sample_volume_from_loops(loops, extent=args.extent, n=args.n, z_extent=args.z_extent, nz=args.nz)
        np.savez_compressed(cache, X=X, Y=Y, Z=Z, Bmag=Bmag)
    kpi = volumetric_kpis(Bmag)
    # Coverage fraction within ±pct of mean
    pct = args.uniformity_pct / 100.0
    mean = kpi["B_mean_T"]
    lo, hi = (1.0 - pct) * mean, (1.0 + pct) * mean
    cover = float(np.mean((Bmag >= lo) & (Bmag <= hi)))
    kpi["coverage_fraction"] = cover
    # Energy and efficiency (grid-based energy)
    dx = (2*args.extent) / (args.n - 1)
    dy = (2*args.extent) / (args.n - 1)
    dz = (2*args.z_extent) / (args.nz - 1)
    U = stored_magnetic_energy_grid(Bmag, dx, dy, dz)
    eta = efficiency_hts_approx(U_J=U, I=args.I, R_circ_ohm=args.R_circ, duration_s=args.duration)
    kpi["stored_energy_J"] = float(U)
    kpi["hts_efficiency"] = float(eta)
    out = {"kpis": kpi, "assumptions": vars(args), "config_hash": cfg_hash}
    (ROOT/"artifacts"/"volumetric_kpis.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
