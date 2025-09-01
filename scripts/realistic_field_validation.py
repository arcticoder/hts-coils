#!/usr/bin/env python3
"""
Validate HTS coil fields against realistic REBCO critical current limits.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.materials import jc_vs_tb, enhanced_thermal_simulation
from hts.coil import sample_helmholtz_pair_plane, helmholtz_loops


def realistic_optimization_check(N=180, I=45000, R=0.5, T=20):
    """
    Check if current design parameters are realistic given REBCO Jc limits.
    
    Based on literature (SuperPower, 2022; Deissler et al., 2014):
    - Jc0 ~300 A/mm² at 77K, self-field
    - Jc0 ~500-800 A/mm² at 20K, self-field  
    - B0 ~5T for significant field derating
    - Typical REBCO tape: 4mm wide, 0.1mm thick
    """
    print("=== Realistic REBCO Critical Current Validation ===")
    
    # Estimate field at conductor location (approximate)
    # For Helmholtz pair, field near the conductors ~B_center * 1.1
    B_center_est = 4e-7 * np.pi * N * I / (2 * R)  # Rough estimate
    B_conductor = B_center_est * 1.1  # Conservative estimate
    
    print(f"Estimated field at conductor: {B_conductor:.1f} T")
    
    # REBCO parameters from literature
    Jc0_20K = 600e6  # A/m² at 20K, self-field (conservative)
    B0 = 5.0  # T, field scale for derating
    n = 1.5   # Exponent for field derating
    Tc = 90.0  # K
    
    # Calculate Jc at operating conditions
    Jc_actual = jc_vs_tb(T, B_conductor, Tc, Jc0_20K, B0, n)
    print(f"Critical current density at {T}K, {B_conductor:.1f}T: {Jc_actual/1e6:.1f} A/mm²")
    
    # Tape geometry (typical REBCO)
    tape_width = 4e-3  # m
    tape_thickness = 0.1e-3  # m (includes substrate)
    tape_area = tape_width * tape_thickness  # m²
    
    # Maximum current per tape
    I_max_per_tape = Jc_actual * tape_area  # A
    print(f"Maximum current per tape: {I_max_per_tape:.0f} A")
    
    # Number of tapes needed in parallel
    tapes_needed = I / I_max_per_tape
    print(f"Tapes needed in parallel: {tapes_needed:.1f}")
    
    # Check feasibility
    if tapes_needed <= 10:  # Reasonable for winding
        feasible = True
        print("✓ Design is FEASIBLE with current REBCO technology")
    elif tapes_needed <= 20:
        feasible = True
        print("⚠ Design is MARGINAL - requires many parallel tapes")
    else:
        feasible = False
        print("✗ Design EXCEEDS realistic REBCO limits")
        
        # Calculate adjusted current for feasibility
        max_tapes = 10  # Practical limit
        I_adjusted = I_max_per_tape * max_tapes
        B_adjusted = B_center_est * (I_adjusted / I)
        print(f"Adjusted current for feasibility: {I_adjusted:.0f} A")
        print(f"Adjusted field: {B_adjusted:.1f} T")
        
        return {
            'feasible': False,
            'I_original': I,
            'I_adjusted': I_adjusted,
            'B_center_T': B_adjusted,
            'tapes_needed': tapes_needed,
            'Jc_A_per_mm2': Jc_actual / 1e6,
            'I_per_tape_A': I_max_per_tape
        }
    
    # Calculate actual field with realistic current
    loops = helmholtz_loops(I, N, R)
    X, Y, Bz = sample_helmholtz_pair_plane(I, N, R, extent=0.2, n=51)
    B_center_actual = Bz[25, 25]  # Center point
    
    print(f"Actual simulated field: {B_center_actual:.1f} T")
    
    # Compare with fusion/HTS magnet benchmarks
    benchmarks = {
        'SPARC TF coils': 12.2,  # T, on-axis field
        'CFS demo magnet': 20.0,  # T, record for HTS
        '32T all-SC magnet': 32.0,  # T, Zhai et al.
        'CERN ALPHA trap': 1.0,  # T, typical antimatter trap
    }
    
    print("\n=== Comparison with Real Systems ===")
    for system, field in benchmarks.items():
        if abs(B_center_actual - field) / field < 0.2:
            print(f"✓ Similar to {system}: {field} T")
        elif B_center_actual > field * 1.5:
            print(f"⚠ Much higher than {system}: {field} T")
    
    return {
        'feasible': feasible,
        'B_center_T': B_center_actual,
        'Jc_A_per_mm2': Jc_actual / 1e6,
        'tapes_needed': tapes_needed,
        'I_per_tape_A': I_max_per_tape
    }


def main():
    """Run validation for current design parameters."""
    
    # Test current design
    result = realistic_optimization_check(N=180, I=45000, R=0.5, T=20)
    
    print(f"\n=== Summary ===")
    print(f"Field achievable: {result['B_center_T']:.1f} T")
    print(f"Feasible with REBCO: {'YES' if result['feasible'] else 'NO'}")
    
    # Test alternative configurations
    print(f"\n=== Alternative Configurations ===")
    
    configs = [
        (180, 30000, 0.5, 20, "Reduced current"),
        (180, 45000, 0.6, 20, "Larger radius"), 
        (120, 45000, 0.5, 20, "Fewer turns"),
        (180, 45000, 0.5, 15, "Lower temperature")
    ]
    
    for N, I, R, T, desc in configs:
        print(f"\n{desc}: N={N}, I={I:.0f}A, R={R:.1f}m, T={T}K")
        result = realistic_optimization_check(N, I, R, T)
        print(f"  Field: {result['B_center_T']:.1f}T, Feasible: {result['feasible']}")


if __name__ == "__main__":
    main()