#!/usr/bin/env python3
"""
Re-optimize HTS coils with realistic REBCO current limits.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.materials import jc_vs_tb, enhanced_thermal_simulation
from hts.coil import sample_helmholtz_pair_plane


def realistic_grid_search():
    """
    Grid search optimization with realistic REBCO limits.
    """
    print("=== Realistic HTS Coil Optimization ===")
    
    # REBCO tape parameters (conservative, based on literature)
    tape_width = 4e-3  # m
    tape_thickness = 0.1e-3  # m  
    tape_area = tape_width * tape_thickness
    
    Jc0_20K = 500e6  # A/m² at 20K, self-field (conservative)
    T_op = 20.0  # K
    max_tapes_parallel = 10  # Practical winding limit
    
    # Parameter ranges
    N_range = [100, 150, 200, 300]  # turns
    R_range = [0.3, 0.4, 0.5, 0.6, 0.8]  # m
    B_target_min = 1.0  # T (realistic for antimatter traps)
    
    feasible_configs = []
    
    for N in N_range:
        for R in R_range:
            # Estimate field at conductor for Jc calculation
            # Start with conservative current estimate
            I_test = 200  # A, conservative starting point
            
            # Iterate to find realistic current
            for iteration in range(10):
                B_est = 4e-7 * np.pi * N * I_test / (2 * R)
                B_conductor = B_est * 1.2  # Account for field enhancement
                
                # Calculate Jc at operating conditions
                Jc = jc_vs_tb(T_op, B_conductor, Tc=90, Jc0=Jc0_20K, B0=5.0, n=1.5)
                
                # Maximum current per tape
                I_max_per_tape = Jc * tape_area
                
                # Total current with practical tape count
                I_total = I_max_per_tape * max_tapes_parallel
                
                # Converge
                if abs(I_total - I_test) / I_test < 0.1:
                    break
                I_test = 0.7 * I_test + 0.3 * I_total  # Smooth convergence
            
            # Final field calculation
            X, Y, Bz = sample_helmholtz_pair_plane(I_total, N, R, extent=0.1, n=21)
            B_center = Bz[10, 10]  # Center point
            
            # Ripple calculation
            Bz_inner = Bz[8:13, 8:13]  # Inner region
            ripple = np.std(Bz_inner) / np.mean(Bz_inner)
            
            # Thermal validation
            tape_length = 2 * np.pi * R * N * 2  # Helmholtz pair
            thermal = enhanced_thermal_simulation(
                I=I_total, T_base=T_op, conductor_length=tape_length,
                tape_width=tape_width
            )
            
            config = {
                'N': N,
                'I': I_total, 
                'R': R,
                'B_center': B_center,
                'ripple': ripple,
                'Jc_A_per_mm2': Jc / 1e6,
                'tapes_parallel': max_tapes_parallel,
                'thermal_margin_K': thermal['thermal_margin_K'],
                'feasible': B_center >= B_target_min and ripple < 0.05 and thermal['thermal_margin_K'] > 10
            }
            
            if config['feasible']:
                feasible_configs.append(config)
                print(f"✓ N={N}, R={R:.1f}m, I={I_total:.0f}A -> B={B_center:.2f}T, ripple={ripple:.3f}")
    
    return feasible_configs


def main():
    """Run realistic optimization."""
    configs = realistic_grid_search()
    
    if not configs:
        print("No feasible configurations found!")
        return
    
    print(f"\n=== Found {len(configs)} Feasible Configurations ===")
    
    # Sort by field strength
    configs.sort(key=lambda x: x['B_center'], reverse=True)
    
    print("\nTop 5 configurations by field strength:")
    for i, cfg in enumerate(configs[:5]):
        print(f"{i+1}. N={cfg['N']}, R={cfg['R']:.1f}m, I={cfg['I']:.0f}A")
        print(f"   B={cfg['B_center']:.2f}T, ripple={cfg['ripple']:.3f}, thermal_margin={cfg['thermal_margin_K']:.1f}K")
        print(f"   Jc={cfg['Jc_A_per_mm2']:.0f} A/mm², {cfg['tapes_parallel']} tapes parallel")
    
    # Best overall (balance of field and ripple)
    best = min(configs, key=lambda x: x['ripple'] + 0.1 / x['B_center'])
    
    print(f"\n=== Recommended Configuration ===")
    print(f"N = {best['N']} turns per coil")
    print(f"R = {best['R']:.1f} m radius") 
    print(f"I = {best['I']:.0f} A per turn")
    print(f"Field = {best['B_center']:.2f} T")
    print(f"Ripple = {best['ripple']:.3f} ({best['ripple']*100:.1f}%)")
    print(f"Thermal margin = {best['thermal_margin_K']:.1f} K")
    print(f"Critical current density = {best['Jc_A_per_mm2']:.0f} A/mm²")
    
    # Compare to applications
    print(f"\n=== Application Comparison ===")
    apps = {
        'CERN ALPHA trap': (1.0, 'antimatter trapping'),
        'AEgIS experiment': (1.0, 'antimatter gravity tests'),
        'Penning trap': (5.0, 'ion confinement'),
        'NMR magnet': (9.4, 'analytical chemistry')
    }
    
    for app_name, (field, desc) in apps.items():
        if best['B_center'] >= field * 0.8:
            print(f"✓ Suitable for {app_name} ({desc}): requires {field} T")


if __name__ == "__main__":
    main()