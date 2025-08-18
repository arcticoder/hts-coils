#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import sys
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_circular_coil_plane, sample_helmholtz_pair_plane  # type: ignore
from hts.config import load_config  # type: ignore


def kpis(B):
    m = float(np.nanmean(B)); s = float(np.nanstd(B))
    return {"B_mean_T": m, "B_std_T": s, "ripple_rms": float(s/(abs(m)+1e-18))}


def objective(params, geom: str, extent: float, n: int):
    N, I, R = int(params[0]), float(params[1]), float(params[2])
    if geom == "helmholtz":
        sep = float(params[3])
        _, _, Bz = sample_helmholtz_pair_plane(I=I, N=N, R=R, separation=sep, extent=extent, n=n)
    else:
        _, _, Bz = sample_circular_coil_plane(I=I, N=N, R=R, extent=extent, n=n)
    m = kpis(Bz)
    penalty = 0.0 if m["B_mean_T"] >= 5.0 else (5.0 - m["B_mean_T"])**2
    return m["ripple_rms"] + penalty


def main():
    import argparse
    p = argparse.ArgumentParser(description="Optimize coil parameters to minimize ripple with B>=5T")
    p.add_argument("--geom", choices=["single","helmholtz"], default="helmholtz")
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--out", type=Path, default=ROOT/"artifacts"/"best_config.json")
    p.add_argument("--extent", type=float, default=0.2)
    p.add_argument("--n", type=int, default=81)
    p.add_argument("--iters", type=int, default=25)
    args = p.parse_args()

    (ROOT/"artifacts").mkdir(exist_ok=True)

    cfg, _ = load_config(args.config, {"geom": args.geom})
    geom = cfg.get("geom", args.geom)

    try:
        from skopt import gp_minimize
        from skopt.space import Integer, Real
    except Exception:
        gp_minimize = None

    # Define bounds
    space = [Integer(100, 1000, name="N"), Real(1e3, 1e5, name="I"), Real(0.05, 1.0, name="R")]
    if geom == "helmholtz":
        space.append(Real(0.8, 1.2, name="sep_frac"))

    def f(x):
        if geom == "helmholtz":
            N,I,R,sep_frac = x
            sep = sep_frac * R
            return objective([N,I,R,sep], geom, args.extent, args.n)
        else:
            return objective(x, geom, args.extent, args.n)

    best = None
    if gp_minimize is not None:
        res = gp_minimize(f, space, n_calls=args.iters, random_state=42)
        x = res.x
        if geom == "helmholtz":
            N,I,R,sep_frac = x
            sep = sep_frac * R
            _, _, Bz = sample_helmholtz_pair_plane(I=I,N=N,R=R,separation=sep,extent=args.extent,n=args.n)
            m = kpis(Bz)
            best = {"geom": geom, "N": int(N), "I": float(I), "R": float(R), "sep": float(sep), **m}
        else:
            N,I,R = x
            _, _, Bz = sample_circular_coil_plane(I=I,N=N,R=R,extent=args.extent,n=args.n)
            m = kpis(Bz)
            best = {"geom": geom, "N": int(N), "I": float(I), "R": float(R), **m}
    else:
        # Fallback: random grid
        rng = np.random.default_rng(42)
        Ns = rng.integers(100, 1001, size=100)
        Is = rng.uniform(1e3, 1e5, size=100)
        Rs = rng.uniform(0.05, 1.0, size=100)
        for N,I,R in zip(Ns, Is, Rs):
            if geom == "helmholtz":
                sep = float(rng.uniform(0.8, 1.2) * R)
                _, _, Bz = sample_helmholtz_pair_plane(I=I,N=int(N),R=R,separation=sep,extent=args.extent,n=args.n)
                m = kpis(Bz)
                row = {"geom": geom, "N": int(N), "I": float(I), "R": float(R), "sep": float(sep), **m}
            else:
                _, _, Bz = sample_circular_coil_plane(I=I,N=int(N),R=R,extent=args.extent,n=args.n)
                m = kpis(Bz)
                row = {"geom": geom, "N": int(N), "I": float(I), "R": float(R), **m}
            if (best is None) or (row["ripple_rms"] < best["ripple_rms"] and row["B_mean_T"] >= 5.0):
                best = row

    if best is None:
        print(json.dumps({"status": "no_feasible"}))
        return

    args.out.write_text(json.dumps(best, indent=2))
    print(json.dumps({"status": "ok", "best_path": str(args.out), "best": best}, indent=2))


if __name__ == "__main__":
    main()
