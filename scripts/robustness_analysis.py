#!/usr/bin/env python3
"""
Tolerance analysis and robustness studies for HTS coil configurations.
Analyzes sensitivity to parameter variations and manufacturing tolerances.
"""
from __future__ import annotations
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.hts.coil import hts_coil_field, sample_helmholtz_pair_plane
from scripts.config_manager import CoilConfig, config_hash


def monte_carlo_tolerance(config: CoilConfig, tolerances: Dict[str, float], 
                         n_samples: int = 100) -> Dict[str, Any]:
    """
    Perform Monte Carlo analysis with parameter tolerances.
    
    Args:
        config: Baseline configuration
        tolerances: Dict of parameter -> fractional tolerance (e.g., {'R': 0.01} for 1%)
        n_samples: Number of Monte Carlo samples
        
    Returns:
        Dict with statistics on field variations
    """
    print(f"Running Monte Carlo tolerance analysis ({n_samples} samples)...")
    
    # Get baseline field  
    baseline_field = get_field_for_config(config, None)
    baseline_stats = analyze_field_uniformity(baseline_field, config)
    
    # Monte Carlo samples
    field_means = []
    field_ripples = []
    
    for i in range(n_samples):
        # Perturb parameters
        perturbed_config = perturb_config(config, tolerances)
        
        # Compute field
        sample_field = get_field_for_config(perturbed_config, None)
        sample_stats = analyze_field_uniformity(sample_field, perturbed_config)
        
        field_means.append(sample_stats['B_mean'])
        field_ripples.append(sample_stats['ripple_percent'])
        
        if (i + 1) % 20 == 0:
            print(f"  Completed {i+1}/{n_samples} samples")
    
    # Compile statistics
    results = {
        'baseline': baseline_stats,
        'n_samples': n_samples,
        'tolerances': tolerances,
        'field_mean': {
            'mean': float(np.mean(field_means)),
            'std': float(np.std(field_means)),
            'min': float(np.min(field_means)),
            'max': float(np.max(field_means)),
            'percentile_5': float(np.percentile(field_means, 5)),
            'percentile_95': float(np.percentile(field_means, 95))
        },
        'field_ripple': {
            'mean': float(np.mean(field_ripples)),
            'std': float(np.std(field_ripples)),
            'min': float(np.min(field_ripples)),
            'max': float(np.max(field_ripples)),
            'percentile_5': float(np.percentile(field_ripples, 5)),
            'percentile_95': float(np.percentile(field_ripples, 95))
        }
    }
    
    return results


def perturb_config(config: CoilConfig, tolerances: Dict[str, float]) -> CoilConfig:
    """Create a perturbed version of config based on tolerances."""
    import copy
    perturbed = copy.deepcopy(config)
    
    for param, tol in tolerances.items():
        if hasattr(perturbed, param):
            current_val = getattr(perturbed, param)
            if isinstance(current_val, (int, float)):
                # Add random perturbation
                perturbation = np.random.normal(0, tol) * current_val
                new_val = current_val + perturbation
                setattr(perturbed, param, new_val)
    
    return perturbed


def get_field_for_config(config: CoilConfig, coords: np.ndarray = None) -> np.ndarray:
    """Compute magnetic field for given configuration and coordinates."""
    if config.geometry == "helmholtz":
        # Use Helmholtz pair - returns (B_z_grid, r_vals, z_vals)
        B_z_grid, r_vals, z_vals = sample_helmholtz_pair_plane(
            config.I, config.N, config.R, config.separation,
            config.extent, config.n_grid
        )
        return B_z_grid
    else:
        # Single coil
        if coords is None:
            r_vals = np.linspace(-config.extent, config.extent, config.n_grid)
            coords = np.column_stack([r_vals, np.zeros(len(r_vals)), np.zeros(len(r_vals))])
        loops = [{'N': config.N, 'I': config.I, 'R': config.R, 'z': 0.0}]
        B_field = hts_coil_field(loops, coords)
        return np.sqrt(np.sum(B_field**2, axis=1))


def analyze_field_uniformity(B_field: np.ndarray, config: CoilConfig) -> Dict[str, float]:
    """Analyze field uniformity and return statistics."""
    # If 2D array from sample_helmholtz_pair_plane, take center slice
    if B_field.ndim == 2:
        center_idx = B_field.shape[0] // 2
        B_center_line = B_field[center_idx, :]
    else:
        B_center_line = B_field
    
    B_mean = np.mean(B_center_line)
    B_min = np.min(B_center_line)
    B_max = np.max(B_center_line)
    ripple = (B_max - B_min) / B_mean if B_mean > 0 else 0
    
    return {
        'B_mean': float(B_mean),
        'B_min': float(B_min),
        'B_max': float(B_max),
        'ripple_percent': float(ripple * 100)
    }


def sensitivity_analysis(config: CoilConfig, params: List[str], 
                        delta_percent: float = 1.0) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by varying each parameter individually.
    
    Args:
        config: Baseline configuration
        params: List of parameter names to vary
        delta_percent: Percentage change for sensitivity calculation
        
    Returns:
        Dict with sensitivity coefficients
    """
    print(f"Running sensitivity analysis (±{delta_percent}% variations)...")
    
    # Get baseline field
    baseline_field = get_field_for_config(config, None)
    baseline_stats = analyze_field_uniformity(baseline_field, config)
    
    sensitivities = {}
    
    for param in params:
        if not hasattr(config, param):
            print(f"Warning: {param} not found in config")
            continue
            
        current_val = getattr(config, param)
        if not isinstance(current_val, (int, float)):
            continue
            
        delta = delta_percent / 100.0 * current_val
        
        # Positive perturbation
        import copy
        config_plus = copy.deepcopy(config)
        setattr(config_plus, param, current_val + delta)
        field_plus = get_field_for_config(config_plus, None)
        stats_plus = analyze_field_uniformity(field_plus, config_plus)
        
        # Negative perturbation
        config_minus = copy.deepcopy(config)
        setattr(config_minus, param, current_val - delta)
        field_minus = get_field_for_config(config_minus, None)
        stats_minus = analyze_field_uniformity(field_minus, config_minus)
        
        # Calculate sensitivities
        dB_mean = (stats_plus['B_mean'] - stats_minus['B_mean']) / (2 * delta)
        dripple = (stats_plus['ripple_percent'] - stats_minus['ripple_percent']) / (2 * delta)
        
        # Normalize by baseline values for relative sensitivity
        sens_B_mean = dB_mean * current_val / baseline_stats['B_mean'] if baseline_stats['B_mean'] > 0 else 0
        sens_ripple = dripple * current_val / baseline_stats['ripple_percent'] if baseline_stats['ripple_percent'] > 0 else 0
        
        sensitivities[param] = {
            'dB_mean_dParam': float(dB_mean),
            'dRipple_dParam': float(dripple),
            'normalized_B_sensitivity': float(sens_B_mean),
            'normalized_ripple_sensitivity': float(sens_ripple),
            'current_value': float(current_val),
            'delta_used': float(delta)
        }
        
        print(f"  {param}: B_sens = {sens_B_mean:.3f}, Ripple_sens = {sens_ripple:.3f}")
    
    results = {
        'baseline': baseline_stats,
        'delta_percent': delta_percent,
        'sensitivities': sensitivities
    }
    
    return results


def robustness_study(config: CoilConfig, tolerance_levels: List[float] = None) -> Dict[str, Any]:
    """
    Study robustness across different tolerance levels.
    
    Args:
        config: Configuration to study
        tolerance_levels: List of tolerance levels to test (as fractions)
        
    Returns:
        Dict with robustness metrics across tolerance levels
    """
    if tolerance_levels is None:
        tolerance_levels = [0.001, 0.005, 0.01, 0.02, 0.05]  # 0.1% to 5%
    
    print("Running robustness study across tolerance levels...")
    
    # Standard manufacturing tolerances for different parameters
    base_tolerances = {
        'R': 0.01,      # 1% radius tolerance
        'I': 0.005,     # 0.5% current tolerance  
        'N': 0.0,       # Turn count is exact (integer)
        'separation': 0.01  # 1% separation tolerance
    }
    
    results = {'tolerance_levels': tolerance_levels, 'studies': []}
    
    for tol_level in tolerance_levels:
        print(f"  Testing tolerance level: {tol_level*100:.1f}%")
        
        # Scale base tolerances by this level
        tolerances = {k: v * tol_level / 0.01 for k, v in base_tolerances.items()}
        
        # Run Monte Carlo for this tolerance level
        mc_results = monte_carlo_tolerance(config, tolerances, n_samples=50)
        
        study_result = {
            'tolerance_level_percent': float(tol_level * 100),
            'tolerances_used': tolerances,
            'field_mean_std_percent': float(mc_results['field_mean']['std'] / mc_results['baseline']['B_mean'] * 100),
            'ripple_95th_percentile': float(mc_results['field_ripple']['percentile_95']),
            'meets_1percent_ripple': bool(mc_results['field_ripple']['percentile_95'] <= 1.0),
            'field_variation_range_T': float(mc_results['field_mean']['percentile_95'] - mc_results['field_mean']['percentile_5'])
        }
        
        results['studies'].append(study_result)
        
        print(f"    Field std: {study_result['field_mean_std_percent']:.3f}%")
        print(f"    Ripple 95th: {study_result['ripple_95th_percentile']:.3f}%")
        print(f"    Meets 1% ripple: {study_result['meets_1percent_ripple']}")
    
    return results


def main():
    """Run tolerance analysis and robustness studies."""
    import argparse
    
    p = argparse.ArgumentParser(description="Tolerance analysis for HTS coil configurations")
    p.add_argument("--config", type=Path, default=None, help="Configuration file")
    p.add_argument("--output", type=Path, default=Path("tolerance_analysis.json"))
    p.add_argument("--monte_carlo", action="store_true", help="Run Monte Carlo analysis")
    p.add_argument("--sensitivity", action="store_true", help="Run sensitivity analysis")
    p.add_argument("--robustness", action="store_true", help="Run robustness study")
    p.add_argument("--samples", type=int, default=100, help="Monte Carlo samples")
    
    args = p.parse_args()
    
    # Use optimal Helmholtz config if no config provided
    if args.config:
        from scripts.config_manager import load_config
        config = load_config(args.config)
    else:
        config = CoilConfig(
            geometry="helmholtz",
            N=200,
            I=40000.0,
            R=0.4,
            separation=0.4,
            extent=0.15,
            n_grid=61
        )
    
    print(f"Analyzing configuration: {config.geometry}")
    print(f"  N={config.N}, I={config.I}A, R={config.R}m")
    print()
    
    results = {'config': config.__dict__, 'config_hash': config_hash(config)}
    
    if args.monte_carlo:
        # Standard manufacturing tolerances
        tolerances = {'R': 0.01, 'I': 0.005, 'separation': 0.01}  # 1%, 0.5%, 1%
        mc_results = monte_carlo_tolerance(config, tolerances, args.samples)
        results['monte_carlo'] = mc_results
        
        print(f"Monte Carlo Results:")
        print(f"  Baseline: B={mc_results['baseline']['B_mean']:.2f}T, Ripple={mc_results['baseline']['ripple_percent']:.3f}%")
        print(f"  Field mean: {mc_results['field_mean']['mean']:.2f} ± {mc_results['field_mean']['std']:.3f}T")
        print(f"  Ripple: {mc_results['field_ripple']['mean']:.3f} ± {mc_results['field_ripple']['std']:.3f}%")
        print(f"  95% of configs have ripple ≤ {mc_results['field_ripple']['percentile_95']:.3f}%")
        print()
    
    if args.sensitivity:
        params = ['N', 'I', 'R', 'separation']
        sens_results = sensitivity_analysis(config, params)
        results['sensitivity'] = sens_results
        
        print("Sensitivity Analysis:")
        for param, sens in sens_results['sensitivities'].items():
            print(f"  {param}: B_sens={sens['normalized_B_sensitivity']:.3f}, Ripple_sens={sens['normalized_ripple_sensitivity']:.3f}")
        print()
    
    if args.robustness:
        rob_results = robustness_study(config)
        results['robustness'] = rob_results
        
        print("Robustness Study:")
        for study in rob_results['studies']:
            print(f"  Tol {study['tolerance_level_percent']:.1f}%: "
                  f"Field_std={study['field_mean_std_percent']:.3f}%, "
                  f"Ripple_95th={study['ripple_95th_percentile']:.3f}%, "
                  f"Meets_1%={study['meets_1percent_ripple']}")
        print()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()