#!/usr/bin/env python3
"""
Bayesian optimization to find HTS coil configurations minimizing ripple with B >= 5T constraint.
"""
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_helmholtz_pair_plane, sample_circular_coil_plane, sample_stack_plane  # type: ignore

try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer, Categorical
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False


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
    
    return {"B_mean_T": B_mean_T, "ripple_rms": ripple_rms}


def grid_optimize(geom: str, max_evaluations: int = 100) -> List[Dict]:
    """Simple grid search optimizer."""
    print(f"Running grid optimization for {geom} geometry...")
    
    # Define search ranges
    if geom == "helmholtz":
        N_range = [200, 300, 400, 500]
        I_range = [20000, 30000, 40000, 50000, 60000]
        R_range = [0.2, 0.25, 0.3, 0.35, 0.4]
    else:
        N_range = [300, 400, 500, 600]
        I_range = [30000, 40000, 50000, 60000, 80000]
        R_range = [0.15, 0.2, 0.25, 0.3]
    
    results = []
    count = 0
    
    for N in N_range:
        for I in I_range:
            for R in R_range:
                if count >= max_evaluations:
                    break
                
                metrics = evaluate_config(geom, N, I, R)
                
                result = {
                    "geometry": geom,
                    "N": N,
                    "I": I,
                    "R": R,
                    **metrics,
                    "feasible": metrics["B_mean_T"] >= 5.0 and metrics["ripple_rms"] <= 0.01
                }
                results.append(result)
                count += 1
                
                if count % 10 == 0:
                    print(f"Evaluated {count}/{max_evaluations} configurations")
            
            if count >= max_evaluations:
                break
        if count >= max_evaluations:
            break
    
    return results


def bayesian_optimize(geom: str, n_calls: int = 50) -> List[Dict]:
    """Bayesian optimization using skopt (if available)."""
    if not SKOPT_AVAILABLE:
        print("skopt not available, falling back to grid search")
        return grid_optimize(geom, max_evaluations=n_calls)
    
    print(f"Running Bayesian optimization for {geom} geometry...")
    
    # Define search space
    if geom == "helmholtz":
        dimensions = [
            Integer(200, 500, name='N'),
            Real(20000, 60000, name='I'),
            Real(0.2, 0.4, name='R'),
        ]
    else:
        dimensions = [
            Integer(300, 600, name='N'),
            Real(30000, 80000, name='I'),
            Real(0.15, 0.3, name='R'),
        ]
    
    results = []
    
    @use_named_args(dimensions)
    def objective(**params):
        metrics = evaluate_config(geom, **params)
        B_mean_T = metrics["B_mean_T"]
        ripple_rms = metrics["ripple_rms"]
        
        # Store result
        result = {
            "geometry": geom,
            **params,
            **metrics,
            "feasible": B_mean_T >= 5.0 and ripple_rms <= 0.01
        }
        results.append(result)
        
        # Objective: minimize ripple, with penalty if B < 5T
        penalty = 1000.0 if B_mean_T < 5.0 else 0.0
        return ripple_rms + penalty
    
    # Run optimization
    result = gp_minimize(objective, dimensions, n_calls=n_calls, random_state=42)
    
    return results


def main():
    import argparse
    
    p = argparse.ArgumentParser(description="Optimize HTS coil configuration")
    p.add_argument("--geom", choices=["single", "helmholtz", "stack"], default="helmholtz")
    p.add_argument("--method", choices=["grid", "bayesian"], default="bayesian")
    p.add_argument("--n_calls", type=int, default=50)
    p.add_argument("--output", type=Path, default=ROOT/"artifacts"/"optimization_results.json")
    args = p.parse_args()
    
    (ROOT / "artifacts").mkdir(exist_ok=True)
    
    # Run optimization
    if args.method == "bayesian":
        results = bayesian_optimize(args.geom, n_calls=args.n_calls)
    else:
        results = grid_optimize(args.geom, max_evaluations=args.n_calls)
    
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
            "geometry": args.geom,
            "method": args.method,
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
    print(f"Feasible solutions (B>=5T, ripple<=1%): {len(feasible)}")
    
    if best_feasible:
        print(f"\nBest feasible solution:")
        print(f"  N={best_feasible['N']}, I={best_feasible['I']:.0f}A, R={best_feasible['R']:.3f}m")
        print(f"  B_mean={best_feasible['B_mean_T']:.2f}T, ripple={best_feasible['ripple_rms']:.4f}")
    else:
        print(f"\nNo feasible solutions found in search space.")
        if best_overall:
            print(f"Best overall (ignoring constraints):")
            print(f"  N={best_overall['N']}, I={best_overall['I']:.0f}A, R={best_overall['R']:.3f}m")
            print(f"  B_mean={best_overall['B_mean_T']:.2f}T, ripple={best_overall['ripple_rms']:.4f}")


if __name__ == "__main__":
    main()