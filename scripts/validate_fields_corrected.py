#!/usr/bin/env python3
"""
Corrected magnetic field validation for HTS Helmholtz coils.
Validates numerical Biot-Savart implementation against analytical circular loop formula.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple

from hts.coil import sample_helmholtz_pair_plane, mu_0


def analytical_helmholtz_center(I: float, N: int, R: float, separation: float) -> float:
    """
    Calculate magnetic field at center of Helmholtz pair using correct analytical formula.
    
    Args:
        I: Current in amperes
        N: Number of turns per coil  
        R: Coil radius in meters
        separation: Distance between coil centers in meters
        
    Returns:
        Magnetic field in Tesla at geometric center
    """
    z_coil = separation / 2.0
    # Each circular coil contributes: B = (μ₀ * N * I * R²) / (2 * (R² + z²)^(3/2))
    B_per_coil = (mu_0 * N * I * R**2) / (2 * (R**2 + z_coil**2)**(3/2))
    return 2.0 * B_per_coil  # Superposition of two identical coils


def validate_helmholtz_center(I: float, N: int, R: float, separation: float) -> Dict:
    """Validate center field calculation against analytical solution."""
    # Get numerical result from Biot-Savart implementation
    X, Y, Bz_numerical = sample_helmholtz_pair_plane(I, N, R, separation, 0.01, 21)
    center_idx = 21 // 2
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


def run_comprehensive_validation() -> Dict:
    """Run validation across multiple test configurations."""
    
    # Test cases with realistic parameters
    test_cases = [
        {'name': 'Reference_Helmholtz', 'I': 1.0, 'N': 1, 'R': 1.0, 'separation': 1.0},
        {'name': 'Medium_Scale_Test', 'I': 100.0, 'N': 10, 'R': 0.2, 'separation': 0.2},
        {'name': 'Small_Coil_Test', 'I': 50.0, 'N': 5, 'R': 0.05, 'separation': 0.05}
    ]
    
    print("Running corrected magnetic field validation...")
    print("=" * 60)
    
    results = {}
    all_errors = []
    
    for case in test_cases:
        name = case['name']
        I, N, R, separation = case['I'], case['N'], case['R'], case['separation']
        
        print(f"\n{name}:")
        print(f"  Parameters: I={I}A, N={N}, R={R}m, sep={separation}m")
        
        validation = validate_helmholtz_center(I, N, R, separation)
        results[name] = {'parameters': case, 'validation': validation}
        all_errors.append(validation['rel_error_percent'])
        
        print(f"  Numerical:  {validation['B_numerical']:.6e} T")
        print(f"  Analytical: {validation['B_analytical']:.6e} T")
        print(f"  Rel error:  {validation['rel_error_percent']:.6f}%")
        print(f"  Status:     {'✓ PASS' if validation['validation_passed'] else '✗ FAIL'}")
    
    # Summary statistics
    passed = sum(1 for r in results.values() if r['validation']['validation_passed'])
    total = len(results)
    max_error = max(all_errors)
    avg_error = sum(all_errors) / len(all_errors)
    
    print(f"\n{'=' * 60}")
    print(f"VALIDATION SUMMARY:")
    print(f"  Tests passed: {passed}/{total}")
    print(f"  Success rate: {passed/total*100:.1f}%")
    print(f"  Max rel error: {max_error:.6f}%")
    print(f"  Avg rel error: {avg_error:.6f}%")
    
    if passed == total:
        print("✓ ALL FIELD CALCULATIONS VALIDATED SUCCESSFULLY!")
    else:
        print("⚠ Some validation tests failed - check implementation")
    
    # Generate comprehensive report
    report = {
        'validation_summary': {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': passed/total,
            'max_relative_error_percent': max_error,
            'avg_relative_error_percent': avg_error,
            'validation_method': 'Biot-Savart vs analytical circular loop superposition'
        },
        'test_results': results,
        'notes': {
            'analytical_formula': 'B = 2 * (μ₀NIR²)/(2(R²+z²)^(3/2)) where z = separation/2',
            'numerical_method': 'Biot-Savart discretization with 360 segments per coil',
            'tolerance': '0.1% relative error for validation pass'
        }
    }
    
    return report


def save_validation_report(report: Dict, filepath: str = 'artifacts/field_validation_corrected.json'):
    """Save validation report to JSON file."""
    Path(filepath).parent.mkdir(exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"\nDetailed report saved to: {filepath}")


def main():
    """Main validation routine."""
    print("HTS Coil Magnetic Field Validation")
    print("Validating numerical implementation against analytical solutions")
    print()
    
    # Run validation
    report = run_comprehensive_validation()
    
    # Save results
    save_validation_report(report)
    
    # Return success status
    return report['validation_summary']['success_rate'] == 1.0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)