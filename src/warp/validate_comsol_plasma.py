#!/usr/bin/env python3
"""
COMSOL Plasma Integration Validation Script

This script validates the COMSOL plasma physics integration by running
test simulations and comparing results against analytical solutions.
Ensures <5% validation error requirement is met for production use.

Usage:
    python validate_comsol_plasma.py [--quick] [--detailed]

Options:
    --quick     Run minimal validation (faster, reduced accuracy)
    --detailed  Run comprehensive validation with multiple test cases
"""

import sys
import argparse
import time
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from warp.comsol_plasma import (
        validate_comsol_plasma_integration,
        COMSOLPlasmaSimulator,
        COMSOLPlasmaConfig,
        COMSOLPlasmaResults
    )
    from warp.plasma_simulation import PlasmaParameters
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"❌ Import failed: {e}")
    IMPORTS_SUCCESSFUL = False


def run_quick_validation():
    """Run quick validation test with minimal parameters."""
    print("🚀 Quick Validation Mode")
    print("-" * 30)
    
    if not IMPORTS_SUCCESSFUL:
        return {"success": False, "error": "Import failed"}
    
    try:
        results = validate_comsol_plasma_integration()
        
        # Summarize results
        summary = {
            "success": results.get('overall_success', False),
            "validation_error_percent": results.get('error_percentage', 100.0),
            "execution_time_s": results.get('execution_time_s', 0.0),
            "comsol_available": results.get('comsol_available', False),
            "simulation_converged": results.get('simulation_successful', False)
        }
        
        return summary
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def run_detailed_validation():
    """Run comprehensive validation with multiple test cases."""
    print("🔬 Detailed Validation Mode")
    print("-" * 30)
    
    if not IMPORTS_SUCCESSFUL:
        return {"success": False, "error": "Import failed"}
    
    validation_cases = [
        {
            "name": "Low Density Plasma",
            "params": PlasmaParameters(
                density_m3=1e18,
                temperature_eV=50.0,
                domain_size_m=0.005,
                grid_nx=12, grid_ny=12, grid_nz=12,
                dt_s=1e-8,
                total_time_ms=0.00005,
                coil_field_T=1.0
            )
        },
        {
            "name": "Medium Density Plasma", 
            "params": PlasmaParameters(
                density_m3=1e19,
                temperature_eV=100.0,
                domain_size_m=0.01,
                grid_nx=16, grid_ny=16, grid_nz=16,
                dt_s=1e-8,
                total_time_ms=0.0001,
                coil_field_T=3.0
            )
        },
        {
            "name": "High Density Plasma",
            "params": PlasmaParameters(
                density_m3=5e19,
                temperature_eV=200.0,
                domain_size_m=0.01,
                grid_nx=20, grid_ny=20, grid_nz=20,
                dt_s=5e-9,
                total_time_ms=0.0002,
                coil_field_T=5.0
            )
        }
    ]
    
    config = COMSOLPlasmaConfig(
        plasma_model="fluid",
        mesh_resolution="fine",
        analytical_validation=True,
        error_tolerance=0.05
    )
    
    simulator = COMSOLPlasmaSimulator(config)
    detailed_results = []
    
    for i, case in enumerate(validation_cases):
        print(f"\n📊 Test Case {i+1}: {case['name']}")
        print(f"   Density: {case['params'].density_m3:.1e} m⁻³")
        print(f"   Temperature: {case['params'].temperature_eV:.1f} eV")
        print(f"   Field: {case['params'].coil_field_T:.1f} T")
        
        try:
            start_time = time.time()
            results = simulator.simulate_plasma_soliton_formation(case['params'])
            execution_time = time.time() - start_time
            
            case_results = {
                "name": case['name'],
                "parameters": {
                    "density": case['params'].density_m3,
                    "temperature": case['params'].temperature_eV,
                    "field": case['params'].coil_field_T
                },
                "success": results.converged,
                "validation_error": results.validation_error,
                "validation_passed": results.validation_passed,
                "execution_time_s": execution_time,
                "mesh_nodes": results.mesh_nodes,
                "mesh_elements": results.mesh_elements
            }
            
            detailed_results.append(case_results)
            
            print(f"   Result: {'✅ Pass' if results.validation_passed else '❌ Fail'}")
            print(f"   Error: {results.validation_error*100:.2f}%")
            print(f"   Time: {execution_time:.1f}s")
            
        except Exception as e:
            print(f"   Result: ❌ Exception - {e}")
            detailed_results.append({
                "name": case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Overall assessment
    successful_cases = sum(1 for result in detailed_results 
                          if result.get('validation_passed', False))
    total_cases = len(detailed_results)
    
    summary = {
        "success": successful_cases == total_cases,
        "successful_cases": successful_cases,
        "total_cases": total_cases,
        "success_rate": successful_cases / total_cases if total_cases > 0 else 0.0,
        "average_error": sum(result.get('validation_error', 1.0) for result in detailed_results) / total_cases,
        "detailed_results": detailed_results
    }
    
    return summary


def run_analytical_benchmarks():
    """Run analytical benchmarks for specific plasma physics models."""
    print("📐 Analytical Benchmark Tests")
    print("-" * 30)
    
    benchmarks = {
        "plasma_frequency": {
            "description": "Plasma frequency calculation",
            "test_density": 1e20,  # m^-3
            "expected_freq": 8.98e10,  # rad/s (calculated)
            "tolerance": 0.01
        },
        "cyclotron_frequency": {
            "description": "Electron cyclotron frequency",
            "test_field": 2.0,  # T
            "expected_freq": 3.51e11,  # rad/s (calculated)
            "tolerance": 0.01
        },
        "debye_length": {
            "description": "Plasma Debye length",
            "test_density": 1e20,  # m^-3
            "test_temperature": 100.0,  # eV
            "expected_length": 7.43e-6,  # m (calculated)
            "tolerance": 0.05
        }
    }
    
    benchmark_results = {}
    
    for name, benchmark in benchmarks.items():
        print(f"\n🧮 {benchmark['description']}")
        
        try:
            if name == "plasma_frequency":
                # ωₚ = √(nₑe²/ε₀mₑ)
                n_e = benchmark['test_density']
                e = 1.602e-19  # C
                epsilon_0 = 8.854e-12  # F/m
                m_e = 9.109e-31  # kg
                
                calculated_freq = np.sqrt(n_e * e**2 / (epsilon_0 * m_e))
                
            elif name == "cyclotron_frequency":
                # ωc = eB/mₑ
                B = benchmark['test_field']
                e = 1.602e-19  # C
                m_e = 9.109e-31  # kg
                
                calculated_freq = e * B / m_e
                
            elif name == "debye_length":
                # λD = √(ε₀kBTₑ/nₑe²)
                n_e = benchmark['test_density']
                T_e = benchmark['test_temperature'] * 1.602e-19  # Convert eV to J
                k_B = 1.381e-23  # J/K (but we already converted T to J)
                e = 1.602e-19  # C
                epsilon_0 = 8.854e-12  # F/m
                
                calculated_length = np.sqrt(epsilon_0 * T_e / (n_e * e**2))
            
            # Compare with expected value
            expected = benchmark.get('expected_freq', benchmark.get('expected_length'))
            error = abs(calculated_freq - expected) / expected if 'freq' in name else abs(calculated_length - expected) / expected
            passed = error < benchmark['tolerance']
            
            benchmark_results[name] = {
                "calculated": calculated_freq if 'freq' in name else calculated_length,
                "expected": expected,
                "error": error,
                "passed": passed
            }
            
            print(f"   Calculated: {calculated_freq if 'freq' in name else calculated_length:.2e}")
            print(f"   Expected: {expected:.2e}")
            print(f"   Error: {error*100:.2f}%")
            print(f"   Result: {'✅ Pass' if passed else '❌ Fail'}")
            
        except Exception as e:
            print(f"   Result: ❌ Exception - {e}")
            benchmark_results[name] = {"error": str(e), "passed": False}
    
    # Overall benchmark assessment
    passed_benchmarks = sum(1 for result in benchmark_results.values() 
                           if result.get('passed', False))
    total_benchmarks = len(benchmark_results)
    
    print(f"\n📊 Benchmark Summary: {passed_benchmarks}/{total_benchmarks} passed")
    
    return {
        "benchmarks_passed": passed_benchmarks,
        "total_benchmarks": total_benchmarks,
        "success_rate": passed_benchmarks / total_benchmarks,
        "individual_results": benchmark_results
    }


def main():
    """Main validation script."""
    parser = argparse.ArgumentParser(description="COMSOL Plasma Integration Validation")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick validation (minimal test)")
    parser.add_argument("--detailed", action="store_true",
                       help="Run detailed validation (comprehensive tests)")
    parser.add_argument("--benchmarks", action="store_true",
                       help="Run analytical benchmarks")
    parser.add_argument("--output", type=str,
                       help="Output file for results (JSON format)")
    
    args = parser.parse_args()
    
    # Default to quick validation if no options specified
    if not (args.quick or args.detailed or args.benchmarks):
        args.quick = True
    
    print("🔬 COMSOL Plasma Physics Integration Validation")
    print("=" * 55)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {
        "timestamp": time.time(),
        "validation_mode": [],
        "overall_success": False
    }
    
    # Run selected validation modes
    if args.quick:
        print("\n" + "="*20 + " QUICK VALIDATION " + "="*20)
        all_results["validation_mode"].append("quick")
        quick_results = run_quick_validation()
        all_results["quick_validation"] = quick_results
        
    if args.detailed:
        print("\n" + "="*19 + " DETAILED VALIDATION " + "="*19)
        all_results["validation_mode"].append("detailed")
        detailed_results = run_detailed_validation()
        all_results["detailed_validation"] = detailed_results
        
    if args.benchmarks:
        print("\n" + "="*18 + " ANALYTICAL BENCHMARKS " + "="*18)
        all_results["validation_mode"].append("benchmarks")
        benchmark_results = run_analytical_benchmarks()
        all_results["analytical_benchmarks"] = benchmark_results
    
    # Overall assessment
    success_indicators = []
    
    if args.quick:
        success_indicators.append(quick_results.get("success", False))
    if args.detailed:
        success_indicators.append(detailed_results.get("success", False))
    if args.benchmarks:
        success_indicators.append(benchmark_results.get("success_rate", 0.0) > 0.8)
    
    all_results["overall_success"] = all(success_indicators) if success_indicators else False
    
    # Print final summary
    print("\n" + "="*20 + " FINAL SUMMARY " + "="*20)
    print(f"Validation modes: {', '.join(all_results['validation_mode'])}")
    print(f"Overall result: {'✅ SUCCESS' if all_results['overall_success'] else '❌ FAILED'}")
    
    if args.quick:
        error_pct = quick_results.get("validation_error_percent", 100.0)
        print(f"Quick validation error: {error_pct:.2f}%")
    
    if args.detailed:
        success_rate = detailed_results.get("success_rate", 0.0)
        print(f"Detailed test success rate: {success_rate*100:.1f}%")
    
    if args.benchmarks:
        benchmark_rate = benchmark_results.get("success_rate", 0.0)
        print(f"Benchmark success rate: {benchmark_rate*100:.1f}%")
    
    # Save results if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"Results saved to: {output_path}")
    
    # Exit with appropriate code
    sys.exit(0 if all_results["overall_success"] else 1)


if __name__ == "__main__":
    try:
        import numpy as np
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Validation failed with exception: {e}")
        sys.exit(1)