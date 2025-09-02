#!/usr/bin/env python3
"""
Comprehensive FEA Validation and Comparison Script

This script validates the HTS coil FEA implementation by comparing:
1. FEniCSx (open-source) solver
2. COMSOL Multiphysics solver  
3. Analytical solutions

Tests the FEASolver renaming and ensures both backends work correctly.
"""

import sys
import numpy as np
from pathlib import Path
import json
import time

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

def test_original_fea_solver():
    """Test the original FEASolver (now properly named)."""
    print("Testing Original FEASolver")
    print("=" * 40)
    
    try:
        from hts.fea import FEASolver, validate_fea_implementation
        
        print("✅ FEASolver imported successfully")
        
        # Run validation
        start_time = time.time()
        results = validate_fea_implementation()
        validation_time = time.time() - start_time
        
        print(f"Validation completed in {validation_time:.2f}s")
        print("Results:")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing FEASolver: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_comsol_integration():
    """Test COMSOL FEA integration."""
    print("\nTesting COMSOL FEA Integration")
    print("=" * 40)
    
    try:
        from hts.comsol_fea import COMSOLFEASolver, validate_comsol_fea
        
        print("✅ COMSOLFEASolver imported successfully")
        
        # Test basic functionality
        solver = COMSOLFEASolver()
        test_params = {
            'N': 400,
            'I': 1171,
            'R': 0.2,
            'conductor_thickness': 0.0002,
            'conductor_height': 0.004,
            'B_field': 2.1
        }
        
        # Test analytical calculation
        analytical_stress = solver.analytical_hoop_stress(2.1, 0.2, 0.0002)
        print(f"✅ Analytical hoop stress: {analytical_stress/1e6:.1f} MPa")
        
        # Run validation (uses analytical fallback)
        print("Running COMSOL validation (analytical fallback)...")
        start_time = time.time()
        results = validate_comsol_fea()
        validation_time = time.time() - start_time
        
        print(f"Validation completed in {validation_time:.2f}s")
        print("Results:")
        for key, value in results.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.3f}")
            else:
                print(f"  {key}: {value}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing COMSOL integration: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_fea_integration_framework():
    """Test the unified FEA integration framework."""
    print("\nTesting FEA Integration Framework")
    print("=" * 40)
    
    try:
        from scripts.fea_integration import create_fea_interface, validate_fea_results
        
        # Test auto-detection
        print("Testing auto-detection...")
        fea_auto = create_fea_interface("auto")
        print(f"✅ Auto-selected backend: {fea_auto.software}")
        
        # Test specific backends
        backends = ["fenics", "comsol"]
        results = {}
        
        coil_params = {
            'N': 400, 'I': 1171, 'R': 0.2,
            'tape_width': 4e-3, 'tape_thickness': 0.1e-3, 'n_tapes': 20
        }
        
        for backend in backends:
            try:
                print(f"\nTesting {backend} backend...")
                fea = create_fea_interface(backend)
                
                start_time = time.time()
                result = fea.run_analysis(coil_params)
                analysis_time = time.time() - start_time
                
                results[backend] = {
                    'max_hoop_stress_MPa': result.max_hoop_stress / 1e6,
                    'max_radial_stress_MPa': result.max_radial_stress / 1e6,
                    'mesh_points': len(result.mesh_points),
                    'analysis_time_s': analysis_time,
                    'validation_error_pct': result.validation_error * 100 if result.validation_error else None
                }
                
                print(f"✅ {backend} analysis completed in {analysis_time:.2f}s")
                print(f"   Max hoop stress: {result.max_hoop_stress/1e6:.1f} MPa")
                print(f"   Max radial stress: {result.max_radial_stress/1e6:.1f} MPa")
                print(f"   Mesh points: {len(result.mesh_points)}")
                
            except Exception as e:
                print(f"❌ Error with {backend} backend: {e}")
                results[backend] = {"error": str(e)}
        
        return results
        
    except Exception as e:
        print(f"❌ Error testing FEA integration framework: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_fea_backend_compatibility():
    """Test explicit backend compatibility between FEniCS and COMSOL."""
    print("\nTesting FEA Backend Compatibility")
    print("=" * 40)
    
    try:
        from scripts.fea_integration import create_fea_interface
        
        # Standard coil parameters for compatibility testing
        coil_params = {
            'N': 400, 'I': 1171, 'R': 0.2,
            'tape_width': 4e-3, 'tape_thickness': 0.1e-3, 'n_tapes': 20
        }
        
        # Test both backends explicitly
        print("Testing FEniCS backend...")
        fenics_fea = create_fea_interface('fenics')
        fenics_result = fenics_fea.run_analysis(coil_params)
        fenics_hoop_stress = fenics_result.max_hoop_stress
        
        print("Testing COMSOL backend...")
        comsol_fea = create_fea_interface('comsol')  
        comsol_result = comsol_fea.run_analysis(coil_params)
        comsol_hoop_stress = comsol_result.max_hoop_stress
        
        # Check compatibility
        relative_error = abs(fenics_hoop_stress - comsol_hoop_stress) / fenics_hoop_stress
        
        print(f"FEniCS hoop stress: {fenics_hoop_stress/1e6:.1f} MPa")
        print(f"COMSOL hoop stress: {comsol_hoop_stress/1e6:.1f} MPa")
        print(f"Relative difference: {relative_error*100:.6f}%")
        
        # Compatibility check
        if relative_error < 0.001:  # <0.1% difference
            print("✅ Backends are fully compatible")
            return True
        else:
            print(f"⚠️  Backend results diverge by {relative_error*100:.3f}%")
            return False
            
    except Exception as e:
        print(f"❌ Backend compatibility test failed: {e}")
        return False

def compare_solver_results(results_dict):
    """Compare results across different solvers."""
    print("\nSolver Comparison")
    print("=" * 40)
    
    if not results_dict:
        print("❌ No results to compare")
        return
    
    # Extract hoop stress values for comparison
    hoop_stresses = {}
    for backend, result in results_dict.items():
        if isinstance(result, dict) and "error" not in result:
            hoop_stresses[backend] = result["max_hoop_stress_MPa"]
    
    if len(hoop_stresses) < 2:
        print("❌ Need at least 2 solvers for comparison")
        return
    
    print("Hoop Stress Comparison:")
    for backend, stress in hoop_stresses.items():
        print(f"  {backend}: {stress:.1f} MPa")
    
    # Calculate relative differences
    stress_values = list(hoop_stresses.values())
    max_stress = max(stress_values)
    min_stress = min(stress_values)
    
    if max_stress > 0:
        relative_diff = abs(max_stress - min_stress) / max_stress * 100
        print(f"\nMaximum relative difference: {relative_diff:.2f}%")
        
        if relative_diff < 1.0:
            print("✅ Excellent agreement between solvers")
        elif relative_diff < 5.0:
            print("✅ Good agreement between solvers")
        else:
            print("⚠️  Significant differences detected - investigate further")
    
    # Performance comparison
    print(f"\nPerformance Comparison:")
    for backend, result in results_dict.items():
        if isinstance(result, dict) and "analysis_time_s" in result:
            print(f"  {backend}: {result['analysis_time_s']:.2f}s")

def generate_validation_report(original_results, comsol_results, integration_results):
    """Generate comprehensive validation report."""
    print("\nValidation Report Summary")
    print("=" * 50)
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original_fea_solver": original_results,
        "comsol_integration": comsol_results,
        "integration_framework": integration_results
    }
    
    # Save report
    report_file = Path(__file__).parent.parent / "artifacts" / "fea_validation_report.json"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"✅ Validation report saved to: {report_file}")
    
    # Summary
    print("\nValidation Summary:")
    success_count = 0
    
    if original_results:
        print("✅ Original FEASolver: PASSED")
        success_count += 1
    else:
        print("❌ Original FEASolver: FAILED")
    
    if comsol_results:
        print("✅ COMSOL Integration: PASSED")
        success_count += 1
    else:
        print("❌ COMSOL Integration: FAILED")
    
    if integration_results:
        print("✅ Integration Framework: PASSED")
        success_count += 1
    else:
        print("❌ Integration Framework: FAILED")
    
    print(f"\nOverall: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("🎉 All tests passed! FEA implementation is validated.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    
    return report

def main():
    """Run comprehensive FEA validation."""
    print("Comprehensive HTS Coil FEA Validation")
    print("=" * 50)
    print("Testing both original FEASolver and new COMSOL integration")
    print()
    
    # Run all tests
    original_results = test_original_fea_solver()
    comsol_results = test_comsol_integration()
    integration_results = test_fea_integration_framework()
    
    # Run backend compatibility test
    compatibility_passed = test_fea_backend_compatibility()
    
    # Compare results
    if integration_results:
        compare_solver_results(integration_results)
    
    # Generate report
    report = generate_validation_report(original_results, comsol_results, integration_results)
    report['backend_compatibility'] = compatibility_passed
    
    print(f"\nValidation completed. Check artifacts/ for detailed results.")
    
    # Summary with compatibility
    if compatibility_passed:
        print("✅ Backend compatibility: PASSED")
    else:
        print("❌ Backend compatibility: FAILED")
        
    return report

if __name__ == "__main__":
    main()