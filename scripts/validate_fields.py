#!/usr/bin/env python3
"""
Validate magnetic field calculations against analytical and reference data.
Cross-checks Biot-Savart implementation for Helmholtz configuration accuracy.
"""
from __future__ import annotations
import numpy as np
import json
from pathlib import Path
import sys
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_helmholtz_pair_plane, mu_0


def analytical_helmholtz_center(I: float, N: int, R: float, separation: float) -> float:
    """
    Analytical formula for magnetic field at center of Helmholtz coils.
    For separation = R (standard Helmholtz), field at center is:
    B = (8/5)^(3/2) * μ₀ * N * I / R
    """
    if abs(separation - R) < 1e-6:  # Standard Helmholtz spacing
        B_center = (8/5)**(3/2) * mu_0 * N * I / R
    else:
        # General formula for arbitrary separation
        z1 = -separation / 2
        z2 = +separation / 2
        
        # Field from each coil at center (0,0,0)
        B1 = (mu_0 * N * I * R**2) / (2 * (R**2 + z1**2)**(3/2))
        B2 = (mu_0 * N * I * R**2) / (2 * (R**2 + z2**2)**(3/2))
        B_center = B1 + B2
    
    return float(B_center)


def validate_helmholtz_center(I: float, N: int, R: float, separation: float, 
                             extent: float = 0.01, n: int = 21) -> Dict[str, float]:
    """
    Validate center field calculation against analytical solution.
    """
    # Get numerical result from our implementation
    X, Y, Bz_numerical = sample_helmholtz_pair_plane(I, N, R, separation, extent, n)
    
    # Extract center value (middle of grid)
    center_idx = n // 2
    B_numerical = float(Bz_numerical[center_idx, center_idx])
    
    # Get analytical result
    B_analytical = analytical_helmholtz_center(I, N, R, separation)
    
    # Calculate error metrics
    abs_error = abs(B_numerical - B_analytical)
    rel_error = abs_error / abs(B_analytical) if B_analytical != 0 else float('inf')
    
    return {
        'B_numerical': B_numerical,
        'B_analytical': B_analytical,
        'abs_error': abs_error,
        'rel_error': rel_error,
        'rel_error_percent': rel_error * 100,
        'validation_passed': rel_error < 1e-3  # 0.1% tolerance
    }


def validate_field_uniformity(I: float, N: int, R: float, separation: float) -> Dict[str, float]:
    """
    Validate field uniformity characteristics of Helmholtz configuration.
    """
    extent = R * 0.3  # Sample over 30% of coil radius
    n = 51
    
    X, Y, Bz = sample_helmholtz_pair_plane(I, N, R, separation, extent, n)
    
    # Extract center line (y=0)
    center_idx = n // 2
    Bz_centerline = Bz[center_idx, :]
    
    # Calculate uniformity metrics
    B_mean = float(np.mean(Bz_centerline))
    B_std = float(np.std(Bz_centerline))
    B_min = float(np.min(Bz_centerline))
    B_max = float(np.max(Bz_centerline))
    
    ripple = (B_max - B_min) / B_mean if B_mean > 0 else 0
    uniformity = B_std / B_mean if B_mean > 0 else 0
    
    return {
        'B_mean': B_mean,
        'B_std': B_std,
        'B_min': B_min,
        'B_max': B_max,
        'ripple_percent': ripple * 100,
        'uniformity_rms': uniformity * 100,
        'sampling_extent': extent,
        'separation_over_R': separation / R
    }


def benchmark_against_literature() -> Dict[str, Dict]:
    """
    Compare against known Helmholtz coil configurations from literature.
    """
    # Test cases based on typical Helmholtz configurations
    test_cases = [
        {
            'name': 'Standard_Helmholtz_1A_1turn_1m',
            'I': 1.0,
            'N': 1, 
            'R': 1.0,
            'separation': 1.0,
            'expected_center_field': (8/5)**(3/2) * mu_0 / 1.0  # Analytical
        },
        {
            'name': 'Optimized_HTS_Config',
            'I': 45000.0,
            'N': 180,
            'R': 0.5,
            'separation': 0.5,
            'expected_center_field': None  # Will calculate analytically
        },
        {
            'name': 'Compact_High_Field', 
            'I': 10000.0,
            'N': 100,
            'R': 0.1,
            'separation': 0.1,
            'expected_center_field': None
        }
    ]
    
    results = {}
    
    for case in test_cases:
        name = case['name']
        I, N, R, sep = case['I'], case['N'], case['R'], case['separation']
        
        # Calculate expected field if not provided
        if case['expected_center_field'] is None:
            expected = analytical_helmholtz_center(I, N, R, sep)
        else:
            expected = case['expected_center_field']
        
        # Validate center field
        validation = validate_helmholtz_center(I, N, R, sep)
        
        # Validate uniformity
        uniformity = validate_field_uniformity(I, N, R, sep)
        
        results[name] = {
            'parameters': {'I': I, 'N': N, 'R': R, 'separation': sep},
            'expected_field': expected,
            'validation': validation,
            'uniformity': uniformity
        }
    
    return results


def create_validation_report() -> Dict[str, object]:
    """
    Generate comprehensive validation report.
    """
    print("Running magnetic field validation...")
    
    # Benchmark against literature/analytical solutions
    benchmark_results = benchmark_against_literature()
    
    # Summary statistics
    all_validations = [r['validation'] for r in benchmark_results.values()]
    passed_count = sum(1 for v in all_validations if v['validation_passed'])
    total_count = len(all_validations)
    
    max_rel_error = max(v['rel_error_percent'] for v in all_validations)
    avg_rel_error = sum(v['rel_error_percent'] for v in all_validations) / len(all_validations)
    
    # Generate report
    report = {
        'validation_summary': {
            'total_tests': total_count,
            'passed_tests': passed_count,
            'success_rate': passed_count / total_count if total_count > 0 else 0,
            'max_relative_error_percent': max_rel_error,
            'avg_relative_error_percent': avg_rel_error
        },
        'test_results': benchmark_results,
        'validation_criteria': {
            'relative_error_threshold_percent': 0.1,
            'analytical_comparison': 'Helmholtz center field formula',
            'numerical_method': 'Biot-Savart discretization (360 segments)'
        }
    }
    
    return report


def main():
    """Run validation and save results."""
    import argparse
    
    p = argparse.ArgumentParser(description="Validate HTS magnetic field calculations")
    p.add_argument("--output", type=Path, default=ROOT/"artifacts"/"field_validation.json")
    args = p.parse_args()
    
    (ROOT / "artifacts").mkdir(exist_ok=True)
    
    # Generate validation report
    report = create_validation_report()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    summary = report['validation_summary']
    print(f"\nValidation Results:")
    print(f"  Tests passed: {summary['passed_tests']}/{summary['total_tests']}")
    print(f"  Success rate: {summary['success_rate']*100:.1f}%")
    print(f"  Max relative error: {summary['max_relative_error_percent']:.4f}%")
    print(f"  Avg relative error: {summary['avg_relative_error_percent']:.4f}%")
    
    if summary['success_rate'] == 1.0:
        print("✓ All field calculations validated successfully!")
    else:
        print("⚠ Some validation tests failed - check detailed results")
    
    print(f"\nDetailed results saved to: {args.output}")


if __name__ == "__main__":
    main()