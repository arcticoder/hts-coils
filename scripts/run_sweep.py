#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import csv
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import (
    sample_circular_coil_plane,
    sample_helmholtz_pair_plane,
    sample_stack_plane,
)  # type: ignore
from hts.config import load_config, cache_path_for  # type: ignore
from hts.metrics import field_per_A_turn, energy_per_tesla  # type: ignore


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
    p.add_argument("--sep-frac-min", type=float, default=0.8, help="If sep not provided, sweep sep in [fmin*R,fmax*R]")
    p.add_argument("--sep-frac-max", type=float, default=1.2)
    p.add_argument("--sep-steps", type=int, default=5)
    p.add_argument("--layers", type=int, default=3)
    p.add_argument("--dz", type=float, default=0.2)
    p.add_argument("--out", type=Path, default=ROOT/"artifacts"/"sweep_results.csv")
    p.add_argument("--topk", type=int, default=10)
    p.add_argument("--config", type=Path, default=None, help="Optional JSON config to load (merged with CLI)")
    p.add_argument("--thickness", type=float, default=0.1, help="Assumed slab thickness (m) for energy estimate")
    p.add_argument("--plots", action="store_true", help="Generate ripple histogram and (if possible) centerline plots")
    p.add_argument("--compare-helmholtz", action="store_true", help="Also run single coil for comparison when geom=helmholtz")
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)
    cli_overrides = {
        "geom": args.geom,
        "N": args.N,
        "I": args.I,
        "R": args.R,
        "extent": args.extent,
        "n": args.n,
        "sep": args.sep,
        "sep_frac_min": args.sep_frac_min,
        "sep_frac_max": args.sep_frac_max,
        "sep_steps": args.sep_steps,
        "layers": args.layers,
        "dz": args.dz,
        "thickness": args.thickness,
    }
    cfg, cfg_hash = load_config(args.config, cli_overrides)

    rows = []
    for N in args.N:
        for I in args.I:
            for R in args.R:
                geom = args.geom
                if geom == "single":
                    cache = cache_path_for(cfg_hash, f"plane-single-N{N}-I{I}-R{R}-n{args.n}-ext{args.extent}")
                    if cache.exists():
                        data = np.load(cache)
                        Bz = data["Bz"]
                    else:
                        _, _, Bz = sample_circular_coil_plane(I=I, N=N, R=R, extent=args.extent, n=args.n)
                        np.savez_compressed(cache, Bz=Bz)
                    m = kpis(Bz)
                    rows.append({"geom": geom, "N": N, "I": I, "R": R, **m,
                                 "field_per_A_turn": field_per_A_turn(m["B_mean_T"], N, I),
                                 "energy_per_T": energy_per_tesla(np.mean(Bz**2)/(2*1.2566370614359172e-6)*(2*args.extent)**2*args.thickness, m["B_mean_T"])})
                elif geom == "helmholtz":
                    seps: list[float]
                    if args.sep is not None:
                        seps = [args.sep]
                    else:
                        seps = list(np.linspace(args.sep_frac_min*R, args.sep_frac_max*R, max(2, args.sep_steps)))
                    best = None
                    for s in seps:
                        cache = cache_path_for(cfg_hash, f"plane-helmholtz-N{N}-I{I}-R{R}-s{s:.5f}-n{args.n}-ext{args.extent}")
                        if cache.exists():
                            data = np.load(cache)
                            Bz = data["Bz"]
                        else:
                            _, _, Bz = sample_helmholtz_pair_plane(I=I, N=N, R=R, separation=s, extent=args.extent, n=args.n)
                            np.savez_compressed(cache, Bz=Bz)
                        m = kpis(Bz)
                        row = {"geom": geom, "N": N, "I": I, "R": R, "sep": float(s), **m,
                               "field_per_A_turn": field_per_A_turn(m["B_mean_T"], N, I),
                               "energy_per_T": energy_per_tesla(np.mean(Bz**2)/(2*1.2566370614359172e-6)*(2*args.extent)**2*args.thickness, m["B_mean_T"]) }
                        if (best is None) or (row["ripple_rms"] < best["ripple_rms"]):
                            best = row
                    assert best is not None
                    rows.append(best)
                else:
                    cache = cache_path_for(cfg_hash, f"plane-stack-N{N}-I{I}-R{R}-L{args.layers}-dz{args.dz}-n{args.n}-ext{args.extent}")
                    if cache.exists():
                        data = np.load(cache)
                        Bz = data["Bz"]
                    else:
                        _, _, Bz = sample_stack_plane(I=I, N=N, R=R, layers=args.layers, axial_spacing=args.dz, extent=args.extent, n=args.n)
                        np.savez_compressed(cache, Bz=Bz)
                    m = kpis(Bz)
                    rows.append({"geom": geom, "N": N, "I": I, "R": R, "layers": args.layers, "dz": args.dz, **m,
                                 "field_per_A_turn": field_per_A_turn(m["B_mean_T"], N, I),
                                 "energy_per_T": energy_per_tesla(np.mean(Bz**2)/(2*1.2566370614359172e-6)*(2*args.extent)**2*args.thickness, m["B_mean_T"])})

    # Write CSV
    with open(args.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # Select top-k meeting B>=5T, ripple<=1%
    candidates = [r for r in rows if r["B_mean_T"] >= 5.0 and r["ripple_rms"] <= 0.01]
    candidates.sort(key=lambda r: (r["ripple_rms"], -r["B_mean_T"]))
    topk = candidates[:args.topk]
    top_path = ROOT/"artifacts"/"sweep_topk.json"
    top_path.write_text(json.dumps({"config_hash": cfg_hash, "rows": topk}, indent=2))
    print(json.dumps({"total": len(rows), "candidates": len(candidates), "topk": len(topk), "config_hash": cfg_hash, "csv": str(args.out), "topk_json": str(top_path)}, indent=2))

    # Optional plots and comparison
    if args.plots:
        try:
            import matplotlib.pyplot as plt  # type: ignore
            import math
            # Optional cross-repo plotting helpers
            try:  # pragma: no cover - optional
                from reactor.plotting import quick_scatter  # type: ignore
            except Exception:  # pragma: no cover
                quick_scatter = None  # type: ignore
            ripples = [r["ripple_rms"] for r in rows]
            plt.figure(); plt.hist(ripples, bins=30); plt.xlabel("ripple_rms"); plt.ylabel("count"); plt.title(f"Ripple histogram ({args.geom})")
            hist_path = ROOT/"artifacts"/f"hist_ripple_{args.geom}.png"
            plt.tight_layout(); plt.savefig(hist_path); plt.close()

            # Centerline for best candidate
            cl_path = None
            if len(rows) > 0:
                best = min(rows, key=lambda r: (r.get("ripple_rms", math.inf)))
                # sample along x-axis at y=0,z=0
                xs = np.linspace(-args.extent, args.extent, args.n)
                Bz_line = []
                N,I,R = best["N"], best["I"], best["R"]
                if args.geom == "single":
                    _, _, Bz = sample_circular_coil_plane(I=I,N=N,R=R,extent=args.extent,n=args.n)
                elif args.geom == "helmholtz":
                    sep = best.get("sep", R)
                    _, _, Bz = sample_helmholtz_pair_plane(I=I,N=N,R=R,separation=sep,extent=args.extent,n=args.n)
                else:
                    _, _, Bz = sample_stack_plane(I=I,N=N,R=R,layers=args.layers,axial_spacing=args.dz,extent=args.extent,n=args.n)
                # Extract center row
                mid = Bz.shape[0]//2
                Bz_line = Bz[mid, :]
                plt.figure(); plt.plot(xs, Bz_line); plt.xlabel("x (m)"); plt.ylabel("Bz (T)"); plt.title("Centerline Bz")
                cl_path = ROOT/"artifacts"/f"centerline_{args.geom}.png"
                plt.tight_layout(); plt.savefig(cl_path); plt.close()

            plots_list = [
                {"path": str(hist_path), "caption": "Histogram of ripple across sweep"},
            ]
            if cl_path:
                plots_list.append({"path": str(cl_path), "caption": "Centerline Bz for best candidate"})

            # Optional comparison: for same grid, run single-coil histogram
            if args.compare_helmholtz and args.geom == "helmholtz":
                rows_single = []
                for N in args.N:
                    for I in args.I:
                        for R in args.R:
                            _, _, Bz_s = sample_circular_coil_plane(I=I,N=N,R=R,extent=args.extent,n=args.n)
                            m_s = kpis(Bz_s)
                            rows_single.append(m_s)
                ripples_s = [r["ripple_rms"] for r in rows_single]
                plt.figure(); plt.hist(ripples_s, bins=30, alpha=0.7, label="single"); plt.hist(ripples, bins=30, alpha=0.7, label="helmholtz"); plt.legend(); plt.xlabel("ripple_rms"); plt.ylabel("count"); plt.title("Ripple histogram: Helmholtz vs Single")
                cmp_path = ROOT/"artifacts"/"hist_ripple_compare.png"
                plt.tight_layout(); plt.savefig(cmp_path); plt.close()
                plots_list.append({"path": str(cmp_path), "caption": "Ripple distribution: Helmholtz vs Single"})

            manifest = {
                "config_hash": cfg_hash,
                "plots": plots_list,
            }
            (ROOT/"artifacts"/"plots_manifest.json").write_text(json.dumps(manifest, indent=2))
        except Exception as e:  # pragma: no cover
            print(f"[plots] skipped: {e}")


if __name__ == "__main__":
    main()
