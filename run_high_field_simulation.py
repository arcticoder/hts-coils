#!/usr/bin/env python3
"""
High-Field HTS Coil Simulation Reproduction Script

This script reproduces the 7.07 T high-field results from the corrected analysis.
Designed to validate computational reproducibility with exact dependency versions.

Usage:
    python run_high_field_simulation.py [options]
    
Example:
    python run_high_field_simulation.py --verbose --validate-comsol
"""

import json
import sys
import os
import argparse
from pathlib import Path
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hts.high_field_scaling import scale_hts_coil_field, validate_high_field_parameters, thermal_margin_space
from hts.comsol_fea import validate_high_field_comsol, COMSOLFEASolver

def main():
    parser = argparse.ArgumentParser(description='Run high-field HTS coil simulation')
    parser.add_argument('--output', '-o', default='results/high_field_results.json', 
                        help='Output JSON file for results')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Verbose output')
    parser.add_argument('--validate-comsol', action='store_true',
                        help='Run COMSOL validation (requires COMSOL installation)')
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    
    # High-field configuration parameters (validated 7.07 T design)
    config = {
        'N': 1000,           # Number of turns
        'I': 1800,           # Current per turn (A)
        'R': 0.16,           # Coil radius (m)
        'T_op': 15,          # Operating temperature (K)
        'conductor_thickness': 0.6e-3,  # Multi-tape thickness (m)
        'conductor_height': 4e-3,       # Conductor height (m)
    }
    
    if args.verbose:
        print("🚀 High-Field HTS Coil Simulation")
        print("=" * 40)
        print(f"Configuration: {config}")
        print()
    
    results = {}
    
    # 1. Field Scaling Analysis
    if args.verbose:
        print("🧪 Running field scaling analysis...")
    
    # Create radial evaluation points
    r = np.array([0, 0, 0])  # Center point evaluation
    
    field_result = scale_hts_coil_field(
        r=r,
        N=config['N'], 
        I=config['I'], 
        R=config['R'], 
        T=config['T_op']
    )
    
    results['field_scaling'] = field_result
    
    if args.verbose:
        print(f"   Field magnitude: {field_result['B_magnitude']:.2f} T")
        print(f"   Field ripple: {field_result['ripple']:.4f}")
        print(f"   Current utilization: {field_result['current_utilization']:.2f}")
    
    # 2. Space Thermal Analysis
    if args.verbose:
        print("\n🌡️ Running space thermal analysis...")
    
    coil_params = {
        'T': config['T_op'],
        'R': config['R'],
        'N': config['N'],
        'conductor_height': 0.004,  # 4mm tape height
        'Q_AC': 0.92  # W, AC losses at 1mHz
    }
    
    thermal_result = thermal_margin_space(coil_params, T_env=4)
    
    results['thermal_analysis'] = thermal_result
    
    if args.verbose:
        print(f"   Thermal margin: {thermal_result['thermal_margin_K']:.1f} K")
        print(f"   Final temperature: {thermal_result['T_final']:.2f} K")
        print(f"   Heat load: {thermal_result['heat_load_W']:.2f} W")
    
    # 3. Parameter Validation
    if args.verbose:
        print("\n🔧 Running parameter validation...")
    
    validation_result = validate_high_field_parameters(
        I=config['I'],
        N=config['N'],
        R=config['R'],
        T=config['T_op'],
        B_target=7.0
    )
    
    results['parameter_validation'] = validation_result
    
    if args.verbose:
        print(f"   Parameters valid: {validation_result['parameters_valid']}")
        print(f"   Achieved field: {validation_result['achieved_field_T']:.2f} T")
        print(f"   Hoop stress: {validation_result['hoop_stress_reinforced_MPa']:.1f} MPa")
        print(f"   Reinforced stress: {validation_result['hoop_stress_reinforced_MPa']:.1f} MPa")
        print(f"   Reinforcement factor: {validation_result['reinforcement_factor']:.1f}")
    
    # 4. Optional COMSOL Validation
    if args.validate_comsol:
        if args.verbose:
            print("\n🧪 Running COMSOL validation...")
        
        try:
            solver = COMSOLFEASolver()
            comsol_params = {
                'N': config['N'],
                'I': config['I'],
                'R': config['R'],
                'conductor_thickness': config['conductor_thickness'],
                'conductor_height': config['conductor_height'],
                'B_field': field_result['B_magnitude']
            }
            
            fea_result = solver.compute_electromagnetic_stress(comsol_params)
            results['comsol_validation'] = {
                'max_hoop_stress_MPa': fea_result.max_hoop_stress / 1e6,
                'max_radial_stress_MPa': fea_result.max_radial_stress / 1e6,
                'validation_error': fea_result.validation_error
            }
            
            if args.verbose:
                print(f"   COMSOL hoop stress: {fea_result.max_hoop_stress/1e6:.1f} MPa")
                print(f"   Validation error: {fea_result.validation_error:.6f}")
                
        except Exception as e:
            if args.verbose:
                print(f"   COMSOL validation failed: {e}")
            results['comsol_validation'] = {'error': str(e)}
    
    # 5. Summary
    results['summary'] = {
        'field_target_T': [5.0, 10.0],
        'field_achieved_T': field_result['B_magnitude'],
        'thermal_margin_target_K': 20.0,
        'thermal_margin_achieved_K': thermal_result['thermal_margin_K'],
        'current_utilization_limit': 0.5,
        'current_utilization_achieved': field_result['current_utilization'],
        'stress_limit_MPa': 35.0,
        'stress_achieved_MPa': validation_result['hoop_stress_reinforced_MPa'],
        'all_targets_met': (
            5.0 <= field_result['B_magnitude'] <= 10.0 and
            thermal_result['thermal_margin_K'] >= 20.0 and
            field_result['current_utilization'] <= 0.5 and
            validation_result['hoop_stress_reinforced_MPa'] <= 35.0
        )
    }
    
    # Convert numpy types for JSON serialization
    def convert_for_json(obj):
        if isinstance(obj, dict):
            return {key: convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_for_json(item) for item in obj]
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        else:
            return obj
    
    # Convert results for JSON serialization
    results = convert_for_json(results)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    if args.verbose:
        print(f"\n📊 Results saved to {args.output}")
        print(f"✅ All targets met: {results['summary']['all_targets_met']}")
    
    return results

if __name__ == '__main__':
    results = main()
    if not results['summary']['all_targets_met']:
        sys.exit(1)