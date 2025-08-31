#!/usr/bin/env python3
"""
Stored magnetic energy and efficiency estimates for HTS coils.
"""
from __future__ import annotations
import numpy as np
from typing import Sequence, Tuple, Dict
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import mu_0, field_from_loops  # type: ignore


def estimate_stored_energy(loops: Sequence[Tuple[float, int, float, float]], volume_extent: float = 0.3, n_samples: int = 41) -> float:
    """
    Estimate stored magnetic energy U = (1/2μ₀) ∫ B² dV by sampling B on a cubic grid.
    Returns energy in Joules.
    """
    xs = np.linspace(-volume_extent, volume_extent, n_samples)
    ys = np.linspace(-volume_extent, volume_extent, n_samples)
    zs = np.linspace(-volume_extent, volume_extent, n_samples)
    
    total_b_squared = 0.0
    count = 0
    
    for x in xs:
        for y in ys:
            for z in zs:
                B = field_from_loops(np.array([x, y, z]), loops)
                total_b_squared += np.dot(B, B)
                count += 1
    
    # Volume element
    dV = (2 * volume_extent) ** 3 / (n_samples ** 3)
    # Average B²
    avg_b_squared = total_b_squared / count
    # Total energy
    U = (avg_b_squared / (2 * mu_0)) * (2 * volume_extent) ** 3
    
    return float(U)


def estimate_conductor_mass(loops: Sequence[Tuple[float, int, float, float]], 
                          wire_cross_section_m2: float = 1e-6, 
                          density_kg_m3: float = 8900.0) -> float:
    """
    Rough estimate of conductor mass assuming circular wire cross-section.
    REBCO tapes are more complex, but this gives order of magnitude.
    """
    total_length = 0.0
    for I, N, R, z0 in loops:
        circumference = 2 * np.pi * R
        total_length += N * circumference
    
    volume_m3 = total_length * wire_cross_section_m2
    mass_kg = volume_m3 * density_kg_m3
    return float(mass_kg)


def efficiency_metrics(loops: Sequence[Tuple[float, int, float, float]], 
                      B_mean_T: float,
                      wire_cross_section_m2: float = 1e-6,
                      **kwargs) -> Dict[str, float]:
    """
    Compute efficiency-related metrics:
    - Stored energy (J)
    - Field per A-turn (T per A-turn)
    - Energy per Tesla (J/T)
    - Mass estimate (kg)
    """
    U_J = estimate_stored_energy(loops, **kwargs)
    mass_kg = estimate_conductor_mass(loops, wire_cross_section_m2)
    
    # Total A-turns
    total_a_turns = sum(abs(I) * N for I, N, R, z0 in loops)
    
    metrics = {
        "stored_energy_J": U_J,
        "mass_estimate_kg": mass_kg,
        "total_A_turns": float(total_a_turns),
        "field_per_A_turn": B_mean_T / max(1.0, total_a_turns),
        "energy_per_Tesla": U_J / max(1e-6, B_mean_T),
        "energy_per_mass": U_J / max(1e-6, mass_kg),
    }
    
    return metrics


def main():
    import argparse
    import json
    
    p = argparse.ArgumentParser(description="Compute stored energy and efficiency metrics")
    p.add_argument("--geom", choices=["single", "helmholtz", "stack"], default="single")
    p.add_argument("--I", type=float, default=20000.0)
    p.add_argument("--N", type=int, default=400)
    p.add_argument("--R", type=float, default=0.3)
    p.add_argument("--sep", type=float, default=None)
    p.add_argument("--layers", type=int, default=3)
    p.add_argument("--dz", type=float, default=0.2)
    p.add_argument("--extent", type=float, default=0.3)
    p.add_argument("--n_samples", type=int, default=21)
    p.add_argument("--wire_area", type=float, default=1e-6, help="Wire cross-section m²")
    args = p.parse_args()
    
    # Create loop configuration
    if args.geom == "single":
        loops = [(args.I, args.N, args.R, 0.0)]
    elif args.geom == "helmholtz":
        sep = args.sep or args.R
        z = sep / 2.0
        loops = [(args.I, args.N, args.R, -z), (args.I, args.N, args.R, +z)]
    else:  # stack
        offsets = np.linspace(-(args.layers - 1) / 2.0, (args.layers - 1) / 2.0, args.layers) * args.dz
        loops = [(args.I, args.N, args.R, float(z0)) for z0 in offsets]
    
    # Quick B field estimate at center
    B_center = field_from_loops(np.array([0.0, 0.0, 0.0]), loops)
    B_mean_T = np.linalg.norm(B_center)
    
    # Compute metrics
    metrics = efficiency_metrics(loops, B_mean_T, 
                               wire_cross_section_m2=args.wire_area,
                               volume_extent=args.extent, 
                               n_samples=args.n_samples)
    
    result = {
        "configuration": {
            "geometry": args.geom,
            "loops": loops,
            "B_center_T": float(B_mean_T)
        },
        "efficiency_metrics": metrics,
        "assumptions": {
            "wire_cross_section_m2": args.wire_area,
            "conductor_density_kg_m3": 8900.0,
            "HTS_resistance": "assumed negligible"
        }
    }
    
    (ROOT / "artifacts").mkdir(exist_ok=True)
    output_path = ROOT / "artifacts" / "energy_efficiency_metrics.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()