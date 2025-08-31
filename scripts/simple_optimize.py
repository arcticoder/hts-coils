#!/usr/bin/env python3
"""
Simple optimization script to find HTS coil configurations minimizing ripple with B >= 5T constraint.
Uses grid search instead of Bayesian optimization to avoid dependency issues.
"""
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_helmholtz_pair_plane, sample_circular_coil_plane, sample_stack_plane
from hts.materials import feasibility_summary


def evaluate_config(geom: str, N: int, I: float, R: float, **kwargs) -> Dict[str, float]:
    """Evaluate a configuration and return B_mean_T and ripple_rms."""
    extent = kwargs.get('extent', 0.15)
    n = kwargs.get('n', 61)
    
    if geom == "single":
        _, _, Bz = sample_circular_coil_plane(I=I, N=N, R=R, extent=extent, n=n)
    elif geom == "helmholtz":
        sep = kwargs.get('separation', R)
        _, _, Bz = sample_helmholtz_pair_plane(I=I, N=N, R=R, separation=sep, extent=extent, n=n)
    elif geom == "stack":
        layers = kwargs.get('layers', 3)
        dz = kwargs.get('axial_spacing', 0.2)
        _, _, Bz = sample_stack_plane(I=I, N=N, R=R, layers=layers, axial_spacing=dz, extent=extent, n=n)
    else:
        raise ValueError(f"Unknown geometry: {geom}")
    
    B_mean_T = float(np.nanmean(Bz))
    B_std_T = float(np.nanstd(Bz))
    ripple_rms = float(B_std_T / (abs(B_mean_T) + 1e-18))
    
    # Add thermal feasibility check
    conductor_length = 2 * np.pi * R * N  # Single loop
    if geom == "helmholtz":
        conductor_length *= 2  # Two loops
    elif geom == "stack":
        conductor_length *= kwargs.get('layers', 3)
    
    feas = feasibility_summary(
        B_mean_T=B_mean_T,
        ripple_rms=ripple_rms, 
        T=20.0,  # K
        Tc=90.0,  # K
        Jc0=1e9,  # A/m²
        B_char_T=B_mean_T,
        heat_capacity_j_per_k=1000.0,
        ohmic_w=1e-3,  # mW heat load
        conductor_length=conductor_length
    )
    
    return {
        "B_mean_T": B_mean_T, 
        "ripple_rms": ripple_rms,
        "feasible": all(feas['gates'].values()),
        "thermal_margin_K": feas['derived']['thermal_margin_mk'] / 1000.0,
        "conductor_length_m": conductor_length
    }


def grid_optimize_helmholtz(max_evaluations: int = 100) -> List[Dict]:
    """Grid search optimization for Helmholtz geometry."""
    print("Running grid optimization for Helmholtz geometry...")
    
    # Fine-tune search around known good region
    N_range = [180, 200, 220, 250, 300]
    I_range = [35000, 40000, 45000, 50000, 55000]
    R_range = [0.35, 0.4, 0.45, 0.5]
    
    results = []
    count = 0
    
    for N in N_range:
        for I in I_range:
            for R in R_range:
                if count >= max_evaluations:
                    break
                
                try:
                    metrics = evaluate_config("helmholtz", N, I, R)
                    
                    result = {
                        "geometry": "helmholtz",
                        "N": N,
                        "I": I, 
                        "R": R,
                        "separation": R,  # Standard Helmholtz spacing
                        **metrics
                    }
                    results.append(result)
                    count += 1
                    
                    if count % 5 == 0:
                        print(f"Evaluated {count}/{max_evaluations} configurations")
                        if result['feasible']:
                            print(f"  Found feasible: N={N}, I={I}, R={R:.2f}, B={result['B_mean_T']:.2f}T, ripple={result['ripple_rms']:.4f}")
                            
                except Exception as e:
                    print(f"Error evaluating N={N}, I={I}, R={R}: {e}")
                    
            if count >= max_evaluations:
                break
        if count >= max_evaluations:
            break
    
    return results


def main():
    import argparse
    
    p = argparse.ArgumentParser(description="Simple HTS coil optimization")
    p.add_argument("--n_calls", type=int, default=60)
    p.add_argument("--output", type=Path, default=ROOT/"artifacts"/"optimization_results.json")
    args = p.parse_args()
    
    (ROOT / "artifacts").mkdir(exist_ok=True)
    
    # Run grid optimization
    results = grid_optimize_helmholtz(max_evaluations=args.n_calls)
    
    # Find feasible solutions
    feasible = [r for r in results if r["feasible"]]
    feasible.sort(key=lambda x: x["ripple_rms"])
    
    # Find best overall (minimum ripple among those with B >= 5T)
    best_feasible = feasible[0] if feasible else None
    
    # Best regardless of feasibility (for reference)
    all_sorted = sorted(results, key=lambda x: x["ripple_rms"])
    best_overall = all_sorted[0] if all_sorted else None
    
    summary = {
        "optimization_summary": {
            "geometry": "helmholtz",
            "method": "grid_search",
            "total_evaluations": len(results),
            "feasible_solutions": len(feasible),
            "best_feasible": best_feasible,
            "best_overall": best_overall
        },
        "all_results": results
    }
    
    with open(args.output, "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nOptimization complete!")
    print(f"Total evaluations: {len(results)}")
    print(f"Feasible solutions (B>=5T, ripple<=1%, thermal OK): {len(feasible)}")
    
    if best_feasible:
        print(f"\nBest feasible solution:")
        print(f"  N={best_feasible['N']}, I={best_feasible['I']:.0f}A, R={best_feasible['R']:.3f}m")
        print(f"  B_mean={best_feasible['B_mean_T']:.2f}T, ripple={best_feasible['ripple_rms']:.4f}")
        print(f"  Thermal margin={best_feasible['thermal_margin_K']:.1f}K")
        print(f"  Conductor length={best_feasible['conductor_length_m']:.0f}m")
    else:
        print(f"\nNo feasible solutions found in search space.")
        if best_overall:
            print(f"Best overall (ignoring constraints):")
            print(f"  N={best_overall['N']}, I={best_overall['I']:.0f}A, R={best_overall['R']:.3f}m")
            print(f"  B_mean={best_overall['B_mean_T']:.2f}T, ripple={best_overall['ripple_rms']:.4f}")


if __name__ == "__main__":
    main()