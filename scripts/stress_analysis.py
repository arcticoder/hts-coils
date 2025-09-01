#!/usr/bin/env python3
"""
FEA-like stress analysis for REBCO HTS coils using analytical methods.
"""
from __future__ import annotations
import numpy as np
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def hoop_stress_analysis(B: float, R: float, thickness: float = 0.002) -> dict:
    """
    Calculate hoop stress in HTS coil conductor.
    
    Args:
        B: Magnetic field (T)
        R: Coil radius (m)  
        thickness: Conductor thickness (m)
        
    Returns:
        Dict with stress analysis results
    """
    mu_0 = 4e-7 * np.pi
    
    # Hoop stress from magnetic pressure
    # σ_hoop = B²/(2μ₀) for thin-walled cylinder
    magnetic_pressure = B**2 / (2 * mu_0)  # Pa
    
    # For thick conductor, stress concentration
    # σ_hoop ≈ (B²R)/(2μ₀t) where t is thickness
    if thickness > 0:
        sigma_hoop = magnetic_pressure * R / thickness  # Pa
    else:
        sigma_hoop = magnetic_pressure
    
    # REBCO tape limits from literature
    sigma_delamination_limit = 35e6  # Pa (35 MPa - typical delamination)
    sigma_irreversible_limit = 150e6  # Pa (150 MPa - irreversible degradation)
    sigma_ultimate = 700e6  # Pa (700 MPa - ultimate tensile strength)
    
    return {
        'magnetic_pressure_Pa': magnetic_pressure,
        'hoop_stress_Pa': sigma_hoop,
        'hoop_stress_MPa': sigma_hoop / 1e6,
        'delamination_margin': sigma_delamination_limit / sigma_hoop if sigma_hoop > 0 else float('inf'),
        'irreversible_margin': sigma_irreversible_limit / sigma_hoop if sigma_hoop > 0 else float('inf'),
        'ultimate_margin': sigma_ultimate / sigma_hoop if sigma_hoop > 0 else float('inf'),
        'safe_delamination': sigma_hoop < sigma_delamination_limit,
        'safe_irreversible': sigma_hoop < sigma_irreversible_limit,
        'safe_ultimate': sigma_hoop < sigma_ultimate
    }


def radial_stress_fem_approximation(B: float, R: float, N: int, I: float) -> dict:
    """
    Finite-element-like approximation of radial stress distribution.
    Using analytical solutions for current-carrying coils.
    """
    mu_0 = 4e-7 * np.pi
    
    # Radial positions
    r_inner = R - 0.01  # Inner edge
    r_outer = R + 0.01  # Outer edge
    r_points = np.linspace(r_inner, r_outer, 21)
    
    # Maxwell stress tensor approach
    # T_rr = (1/μ₀)[B_r² - ½(B_r² + B_θ² + B_z²)]
    # Approximate field components for circular coil
    
    stresses_radial = []
    stresses_hoop = []
    
    for r in r_points:
        # Field approximation at radius r
        B_r = 0.1 * B * (r - R) / R  # Radial component (small)
        B_theta = 0  # Azimuthal (zero for axisymmetric)
        B_z = B * (R / r)**2  # Axial component (scales roughly)
        
        B_total_sq = B_r**2 + B_theta**2 + B_z**2
        
        # Maxwell stress components
        T_rr = (1/mu_0) * (B_r**2 - 0.5 * B_total_sq)
        T_theta_theta = (1/mu_0) * (B_theta**2 - 0.5 * B_total_sq)
        
        stresses_radial.append(T_rr)
        stresses_hoop.append(T_theta_theta)
    
    return {
        'r_points_m': r_points,
        'radial_stress_Pa': np.array(stresses_radial),
        'hoop_stress_Pa': np.array(stresses_hoop),
        'max_radial_stress_MPa': np.max(np.abs(stresses_radial)) / 1e6,
        'max_hoop_stress_MPa': np.max(np.abs(stresses_hoop)) / 1e6,
        'stress_concentration_factor': np.max(np.abs(stresses_hoop)) / (B**2/(2*mu_0))
    }


def mechanical_validation(B: float = 2.1, R: float = 0.2, N: int = 400, I: float = 1171):
    """
    Complete mechanical validation of HTS coil design.
    """
    print("=== Mechanical Stress Analysis ===")
    print(f"Design: B={B:.1f}T, R={R:.1f}m, N={N}, I={I:.0f}A")
    
    # Conductor geometry (20 tapes stacked)
    tape_thickness = 0.1e-3  # m per tape
    total_thickness = 20 * tape_thickness  # m
    
    # Hoop stress analysis
    hoop = hoop_stress_analysis(B, R, total_thickness)
    
    print(f"\n--- Hoop Stress Analysis ---")
    print(f"Magnetic pressure: {hoop['magnetic_pressure_Pa']/1e6:.1f} MPa")
    print(f"Hoop stress: {hoop['hoop_stress_MPa']:.1f} MPa")
    print(f"Delamination margin: {hoop['delamination_margin']:.1f}x")
    print(f"Irreversible margin: {hoop['irreversible_margin']:.1f}x")
    print(f"Safe (delamination): {hoop['safe_delamination']}")
    print(f"Safe (irreversible): {hoop['safe_irreversible']}")
    
    # FEA-like radial analysis
    fem_approx = radial_stress_fem_approximation(B, R, N, I)
    
    print(f"\n--- FEA-like Analysis ---")
    print(f"Max radial stress: {fem_approx['max_radial_stress_MPa']:.1f} MPa")
    print(f"Max hoop stress: {fem_approx['max_hoop_stress_MPa']:.1f} MPa")
    print(f"Stress concentration: {fem_approx['stress_concentration_factor']:.2f}")
    
    # Overall assessment
    overall_safe = (hoop['safe_delamination'] and 
                   fem_approx['max_hoop_stress_MPa'] < 35 and
                   fem_approx['max_radial_stress_MPa'] < 100)
    
    print(f"\n--- Assessment ---")
    print(f"Overall safe: {overall_safe}")
    
    if not overall_safe:
        print("⚠️  RECOMMENDATIONS:")
        if not hoop['safe_delamination']:
            print("  - Reduce field or increase conductor thickness")
        if fem_approx['max_hoop_stress_MPa'] >= 35:
            print("  - Add mechanical support structure")
        if fem_approx['max_radial_stress_MPa'] >= 100:
            print("  - Improve radial support/reinforcement")
    else:
        print("✅ Design meets mechanical safety criteria")
    
    return {
        'hoop_analysis': hoop,
        'fem_approximation': fem_approx,
        'overall_safe': overall_safe
    }


def compare_with_literature():
    """
    Compare results with published HTS magnet stress data.
    """
    print("\n=== Literature Comparison ===")
    
    # Published examples
    examples = [
        {'name': '32T All-SC Magnet', 'B': 32, 'R': 0.05, 'stress_reported': '500 MPa'},
        {'name': 'SPARC TF Coil', 'B': 12, 'R': 1.85, 'stress_reported': '300 MPa'},
        {'name': 'Our Design', 'B': 2.1, 'R': 0.2, 'stress_reported': 'TBD'}
    ]
    
    for ex in examples:
        if ex['name'] != 'Our Design':
            hoop = hoop_stress_analysis(ex['B'], ex['R'])
            print(f"{ex['name']}: Calculated {hoop['hoop_stress_MPa']:.0f} MPa vs {ex['stress_reported']} reported")
        else:
            result = mechanical_validation(ex['B'], ex['R'])
            print(f"{ex['name']}: Calculated {result['hoop_analysis']['hoop_stress_MPa']:.0f} MPa")


if __name__ == "__main__":
    # Analyze realistic design
    result = mechanical_validation()
    
    # Compare with literature
    compare_with_literature()