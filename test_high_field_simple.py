#!/usr/bin/env python3
"""
Simplified test for high-field HTS coil implementation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import numpy as np

# Import our high-field scaling modules
try:
    from hts.high_field_scaling import (
        scale_hts_coil_field,
        thermal_margin_space, 
        validate_high_field_parameters,
        helmholtz_high_field_configuration
    )
    from hts.comsol_fea import validate_high_field_comsol
    print("✅ Successfully imported high-field scaling modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def test_field_scaling():
    """Test field scaling function."""
    print("\n🧪 Testing field scaling...")
    
    # Test at center position
    r = np.array([0, 0, 0])
    
    # High-field parameters
    result = scale_hts_coil_field(r, I=5000, N=600, R=0.15, T=10)
    
    print(f"Field magnitude: {result['B_magnitude']:.2f} T")
    print(f"Field ripple: {result['ripple']:.4f}")
    print(f"Critical current density: {result['J_c']/1e6:.1f} MA/m²")
    print(f"Current utilization: {result['current_utilization']:.2f}")
    print(f"Configuration feasible: {result['feasible']}")
    
    return result['B_magnitude'] > 5.0


def test_thermal_analysis():
    """Test space thermal analysis."""
    print("\n🧪 Testing space thermal analysis...")
    
    coil_params = {
        'T': 10,
        'surface_area': 0.1,
        'Q_AC': 0.92
    }
    
    margin = thermal_margin_space(coil_params, T_env=4)
    
    print(f"Operating temperature: {coil_params['T']} K")
    print(f"Thermal margin: {margin:.2f} K")
    print(f"Adequate margin: {margin > 20}")
    
    return margin > 10


def test_parameter_validation():
    """Test parameter validation."""
    print("\n🧪 Testing parameter validation...")
    
    validation = validate_high_field_parameters(I=5000, N=600, R=0.15, T=10)
    
    print(f"Field magnitude: {validation['field_analysis']['B_magnitude']:.2f} T")
    print(f"Thermal margin: {validation['thermal_margin_space']:.2f} K")
    print(f"Hoop stress (reinforced): {validation['hoop_stress_reinforced']/1e6:.1f} MPa")
    print(f"Overall feasible: {validation['overall_feasible']}")
    
    return validation['overall_feasible']


def test_helmholtz_config():
    """Test Helmholtz configuration."""
    print("\n🧪 Testing Helmholtz configuration...")
    
    config = helmholtz_high_field_configuration(target_field=5.0)
    
    print(f"Configuration keys: {list(config.keys())}")
    print(f"Helmholtz config created: {config is not None}")
    
    return config is not None


def test_comsol_validation():
    """Test COMSOL validation."""
    print("\n🧪 Testing COMSOL validation...")
    
    test_params = {
        'N': 600,
        'I': 5000, 
        'R': 0.15,
        'conductor_thickness': 0.0002,
        'conductor_height': 0.004,
        'B_field': 5.0
    }
    
    try:
        result = validate_high_field_comsol(test_params)
        print(f"Analytical stress: {result['analytical_stress_MPa']:.1f} MPa")
        print(f"Reinforcement needed: {result['reinforcement_needed']}")
        return True
    except Exception as e:
        print(f"COMSOL test error: {e}")
        return False


def main():
    """Run simplified tests."""
    print("🚀 HIGH-FIELD HTS COIL SIMPLE TEST")
    print("=" * 40)
    
    tests = [
        ("Field Scaling", test_field_scaling),
        ("Thermal Analysis", test_thermal_analysis), 
        ("Parameter Validation", test_parameter_validation),
        ("Helmholtz Config", test_helmholtz_config),
        ("COMSOL Validation", test_comsol_validation)
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
            status = "✅ PASS" if results[name] else "❌ FAIL"
            print(f"{name}: {status}")
        except Exception as e:
            print(f"{name}: ❌ ERROR - {e}")
            results[name] = False
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
    
    if passed == total:
        print("🎉 All tests successful!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())