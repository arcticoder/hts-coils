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
    """Test field scaling function with realistic parameters."""
    print("\n🧪 Testing field scaling...")
    
    # Test at center position with realistic current
    r = np.array([0, 0, 0])
    
    # Realistic high-field parameters - optimized for 5T target
    result = scale_hts_coil_field(r, I=1800, N=1000, R=0.16, T=15)
    
    print(f"Field magnitude: {result['B_magnitude']:.2f} T")
    print(f"Field ripple: {result['ripple']:.4f}")
    print(f"Critical current density: {result['J_c']/1e6:.1f} MA/m²")
    print(f"Tapes per turn: {result['tapes_per_turn']}")
    print(f"Single tape I_max: {result['I_max_single_tape']:.0f} A")
    print(f"Total I_max: {result['I_max']:.0f} A")
    print(f"Current utilization: {result['current_utilization']:.2f}")
    print(f"Field feasible: {result['field_feasible']}")
    print(f"Thermal feasible: {result['thermal_feasible']}")
    
    return result['field_feasible'] and result['B_magnitude'] > 4.0


def test_thermal_analysis():
    """Test space thermal analysis with realistic geometry."""
    print("\n🧪 Testing space thermal analysis...")
    
    coil_params = {
        'T': 15,
        'R': 0.16,
        'N': 1000,
        'conductor_height': 0.004,
        'Q_AC': 0.92
    }
    
    thermal_result = thermal_margin_space(coil_params, T_env=4)
    
    print(f"Operating temperature: {coil_params['T']} K")
    print(f"Surface area: {thermal_result['surface_area_m2']:.3f} m²")
    print(f"Thermal margin: {thermal_result['thermal_margin_K']:.2f} K")
    print(f"Final temperature: {thermal_result['T_final']:.2f} K")
    print(f"Heat load: {thermal_result['heat_load_W']:.2f} W")
    print(f"Radiative load: {thermal_result['Q_rad_W']:.4f} W")
    print(f"Cryocooler margin: {thermal_result['cryocooler_margin_W']:.1f} W")
    print(f"Space feasible: {thermal_result['space_feasible']}")
    
    return thermal_result['thermal_margin_K'] > 20


def test_parameter_validation():
    """Test parameter validation with realistic parameters."""
    print("\n🧪 Testing parameter validation...")
    
    validation = validate_high_field_parameters(I=1800, N=1000, R=0.16, T=15, B_target=5.0)
    
    print(f"Target field: {validation['parameters']['B_target']:.1f} T")
    print(f"Achieved field: {validation['achieved_field_T']:.2f} T")
    print(f"Current utilization: {validation['current_utilization']:.2f}")
    print(f"Thermal margin: {validation['thermal_margin_K']:.2f} K")
    print(f"Hoop stress (unreinforced): {validation['hoop_stress_unreinforced_MPa']:.1f} MPa")
    print(f"Hoop stress (reinforced): {validation['hoop_stress_reinforced_MPa']:.1f} MPa")
    print(f"Reinforcement factor: {validation['reinforcement_factor']:.1f}")
    print(f"Parameters valid: {validation['parameters_valid']}")
    
    return validation['parameters_valid']


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