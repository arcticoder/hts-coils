#!/usr/bin/env python3
"""
Monte Carlo sensitivity analysis for HTS coil design parameters.

Quantifies uncertainty propagation and parameter sensitivity for:
- Critical current density variations
- Tape thickness tolerances  
- Cryocooler efficiency uncertainties
- Manufacturing variations
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional, Any
import sys
from pathlib import Path

# Add src to path for imports
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from hts.coil import sample_helmholtz_pair_plane
from hts.materials import jc_vs_tb, enhanced_thermal_simulation


class ParameterDistribution:
    """Represents a parameter distribution for Monte Carlo sampling."""
    
    def __init__(self, name: str, distribution: str, mean: float, std: float, 
                 bounds: Optional[Tuple[float, float]] = None):
        self.name = name
        self.distribution = distribution
        self.mean = mean
        self.std = std
        self.bounds = bounds
        
    def sample(self, n_samples: int) -> np.ndarray:
        """Generate samples from the parameter distribution."""
        if self.distribution == 'normal':
            samples = np.random.normal(self.mean, self.std, n_samples)
        elif self.distribution == 'uniform':
            half_width = self.std * np.sqrt(3)  # Convert std to uniform half-width
            samples = np.random.uniform(self.mean - half_width, self.mean + half_width, n_samples)
        elif self.distribution == 'lognormal':
            # Log-normal with specified mean and std
            mu = np.log(self.mean**2 / np.sqrt(self.std**2 + self.mean**2))
            sigma = np.sqrt(np.log(1 + (self.std / self.mean)**2))
            samples = np.random.lognormal(mu, sigma, n_samples)
        else:
            raise ValueError(f"Unknown distribution: {self.distribution}")
            
        # Apply bounds if specified
        if self.bounds:
            samples = np.clip(samples, self.bounds[0], self.bounds[1])
            
        return samples


def define_parameter_distributions() -> Dict[str, ParameterDistribution]:
    """Define parameter distributions for uncertainty analysis."""
    
    distributions = {
        'Jc0_20K': ParameterDistribution(
            name='Critical Current Density at 20K',
            distribution='normal',
            mean=300e6,  # A/m²
            std=50e6,    # ±50 A/mm² uncertainty
            bounds=(200e6, 400e6)
        ),
        
        'tape_thickness': ParameterDistribution(
            name='REBCO Tape Thickness',
            distribution='normal', 
            mean=0.1e-3,  # 0.1 mm
            std=0.02e-3,  # ±0.02 mm tolerance
            bounds=(0.05e-3, 0.15e-3)
        ),
        
        'cryo_efficiency': ParameterDistribution(
            name='Cryocooler Efficiency',
            distribution='normal',
            mean=0.15,    # 15%
            std=0.05,     # ±5% uncertainty
            bounds=(0.05, 0.25)
        ),
        
        'conductor_width': ParameterDistribution(
            name='Conductor Width',
            distribution='normal',
            mean=4e-3,    # 4 mm standard
            std=0.1e-3,   # ±0.1 mm tolerance
            bounds=(3.5e-3, 4.5e-3)
        ),
        
        'winding_precision': ParameterDistribution(
            name='Winding Position Accuracy',
            distribution='normal',
            mean=0.0,     # Perfect positioning (mean)
            std=0.5e-3,   # ±0.5 mm positioning error
            bounds=(-2e-3, 2e-3)
        ),
        
        'field_inhomogeneity': ParameterDistribution(
            name='Local Field Variation',
            distribution='normal',
            mean=1.0,     # Nominal field multiplication factor
            std=0.05,     # ±5% field variation
            bounds=(0.9, 1.1)
        )
    }
    
    return distributions


def monte_carlo_coil_analysis(n_samples: int = 1000, coil_params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Perform Monte Carlo analysis of HTS coil performance with parameter uncertainties.
    
    Args:
        n_samples: Number of Monte Carlo samples
        coil_params: Base coil parameters (N, I, R, etc.)
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    if coil_params is None:
        coil_params = {
            'N': 400,      # Turns per coil
            'I': 1171,     # Current [A]  
            'R': 0.2,      # Radius [m]
            'T_op': 20,    # Operating temperature [K]
            'B_target': 2.1  # Target field [T]
        }
    
    # Get parameter distributions
    distributions = define_parameter_distributions()
    
    # Generate parameter samples
    samples = {}
    for param_name, dist in distributions.items():
        samples[param_name] = dist.sample(n_samples)
    
    # Arrays to store results
    results = {
        'B_center': np.zeros(n_samples),
        'field_ripple': np.zeros(n_samples),
        'critical_current': np.zeros(n_samples),
        'thermal_margin': np.zeros(n_samples),
        'hoop_stress': np.zeros(n_samples),
        'feasible': np.zeros(n_samples, dtype=bool),
        'cost_factor': np.zeros(n_samples)
    }
    
    # Parameter samples for analysis
    param_samples = {name: values for name, values in samples.items()}
    
    print(f"Running Monte Carlo analysis with {n_samples} samples...")
    
    for i in range(n_samples):
        if i % 100 == 0:
            print(f"  Progress: {i}/{n_samples}")
            
        # Extract parameter values for this sample
        Jc0 = param_samples['Jc0_20K'][i]
        thickness = param_samples['tape_thickness'][i]
        cryo_eff = param_samples['cryo_efficiency'][i]
        width = param_samples['conductor_width'][i]
        pos_error = param_samples['winding_precision'][i]
        field_var = param_samples['field_inhomogeneity'][i]
        
        try:
            # Calculate field with position errors
            R_actual = coil_params['R'] + pos_error
            
            # Calculate critical current with parameter variations
            B_self = 2.0 * coil_params['B_target']  # Approximate self-field
            Jc_actual = jc_vs_tb(coil_params['T_op'], B_self * field_var, 
                                Tc=90, Jc0=Jc0, B0=5.0, n=1.5)
            
            # Number of tapes needed (limited by practical constraints)
            tapes_per_turn = 20  # Fixed for this analysis
            tape_area = tapes_per_turn * width * thickness
            I_c_turn = Jc_actual * tape_area
            I_c_total = I_c_turn  # Single turn equivalent
            
            # Field calculation with variations
            # Simplified field estimate with position errors
            B_nominal = 4e-7 * np.pi * coil_params['N'] * coil_params['I'] / (2 * R_actual)
            B_center = B_nominal * field_var
            
            # Field ripple (increases with position errors)
            base_ripple = 0.001  # 0.1% baseline
            ripple = base_ripple * (1 + abs(pos_error) / (0.5e-3))  # Scales with position error
            
            # Thermal analysis
            thermal_result = enhanced_thermal_simulation(
                coil_params['I'], 
                T_base=coil_params['T_op'],
                cryo_efficiency=cryo_eff
            )
            
            # Hoop stress calculation
            mu0 = 4e-7 * np.pi
            conductor_thickness = tapes_per_turn * thickness
            hoop_stress = (B_center**2 * R_actual) / (2 * mu0 * conductor_thickness) / 1e6  # MPa
            
            # Store results
            results['B_center'][i] = B_center
            results['field_ripple'][i] = ripple
            results['critical_current'][i] = I_c_total
            results['thermal_margin'][i] = thermal_result.get('thermal_margin_K', 0)
            results['hoop_stress'][i] = hoop_stress
            
            # Feasibility criteria
            feasible = (
                coil_params['I'] <= I_c_total * 0.8 and  # Current margin
                hoop_stress <= 35.0 and                   # Stress limit
                thermal_result.get('thermal_margin_K', 0) > 20 and  # Thermal margin
                ripple <= 0.01                            # Field quality
            )
            results['feasible'][i] = feasible
            
            # Cost scaling (primarily from tape thickness variation)
            results['cost_factor'][i] = thickness / distributions['tape_thickness'].mean
            
        except Exception as e:
            # Handle calculation failures
            results['feasible'][i] = False
            print(f"    Warning: Sample {i} failed: {e}")
    
    # Calculate statistics
    statistics = {}
    for key, values in results.items():
        if key != 'feasible':
            valid_values = values[results['feasible']]
            if len(valid_values) > 0:
                statistics[key] = {
                    'mean': np.mean(valid_values),
                    'std': np.std(valid_values),
                    'min': np.min(valid_values),
                    'max': np.max(valid_values),
                    'percentile_5': np.percentile(valid_values, 5),
                    'percentile_95': np.percentile(valid_values, 95)
                }
    
    # Feasibility statistics
    feasible_fraction = np.mean(results['feasible'])
    statistics['feasibility'] = {
        'success_rate': feasible_fraction,
        'failure_rate': 1 - feasible_fraction,
        'total_samples': n_samples,
        'feasible_samples': np.sum(results['feasible'])
    }
    
    # Sensitivity analysis using correlation
    sensitivity = {}
    for param_name in param_samples.keys():
        param_values = param_samples[param_name]
        
        # Calculate correlations with key outputs
        sensitivity[param_name] = {}
        for output_name in ['B_center', 'field_ripple', 'thermal_margin', 'hoop_stress']:
            valid_mask = results['feasible']
            if np.sum(valid_mask) > 10:  # Need sufficient valid samples
                corr_coeff = np.corrcoef(param_values[valid_mask], results[output_name][valid_mask])[0, 1]
                sensitivity[param_name][output_name] = corr_coeff
            else:
                sensitivity[param_name][output_name] = 0.0
    
    return {
        'samples': param_samples,
        'results': results,
        'statistics': statistics,
        'sensitivity': sensitivity,
        'coil_params': coil_params
    }


def plot_sensitivity_analysis(analysis_results: Dict[str, Any]) -> plt.Figure:
    """Generate comprehensive sensitivity analysis plots."""
    
    results = analysis_results['results']
    statistics = analysis_results['statistics']
    sensitivity = analysis_results['sensitivity']
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    # Plot 1: Field strength distribution
    feasible_mask = results['feasible']
    ax = axes[0]
    B_values = results['B_center'][feasible_mask]
    ax.hist(B_values, bins=30, alpha=0.7, color='blue', density=True)
    ax.axvline(statistics['B_center']['mean'], color='red', linestyle='--', label='Mean')
    ax.axvline(statistics['B_center']['percentile_5'], color='orange', linestyle=':', label='5th-95th %ile')
    ax.axvline(statistics['B_center']['percentile_95'], color='orange', linestyle=':')
    ax.set_xlabel('Magnetic Field [T]')
    ax.set_ylabel('Probability Density')
    ax.set_title('Field Strength Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Field ripple distribution
    ax = axes[1]
    ripple_values = results['field_ripple'][feasible_mask] * 100  # Convert to %
    ax.hist(ripple_values, bins=30, alpha=0.7, color='green', density=True)
    ax.axvline(statistics['field_ripple']['mean'] * 100, color='red', linestyle='--', label='Mean')
    ax.set_xlabel('Field Ripple [%]')
    ax.set_ylabel('Probability Density')
    ax.set_title('Field Ripple Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 3: Thermal margin distribution
    ax = axes[2]
    thermal_values = results['thermal_margin'][feasible_mask]
    ax.hist(thermal_values, bins=30, alpha=0.7, color='purple', density=True)
    ax.axvline(statistics['thermal_margin']['mean'], color='red', linestyle='--', label='Mean')
    ax.axvline(20, color='orange', linestyle=':', label='Min Requirement')
    ax.set_xlabel('Thermal Margin [K]')
    ax.set_ylabel('Probability Density')
    ax.set_title('Thermal Margin Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Hoop stress distribution
    ax = axes[3]
    stress_values = results['hoop_stress'][feasible_mask]
    ax.hist(stress_values, bins=30, alpha=0.7, color='red', density=True)
    ax.axvline(statistics['hoop_stress']['mean'], color='red', linestyle='--', label='Mean')
    ax.axvline(35, color='orange', linestyle=':', label='Delamination Limit')
    ax.set_xlabel('Hoop Stress [MPa]')
    ax.set_ylabel('Probability Density')
    ax.set_title('Hoop Stress Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Plot 5: Parameter sensitivity heatmap
    ax = axes[4]
    params = list(sensitivity.keys())
    outputs = ['B_center', 'field_ripple', 'thermal_margin', 'hoop_stress']
    
    # Create sensitivity matrix
    sens_matrix = np.zeros((len(params), len(outputs)))
    for i, param in enumerate(params):
        for j, output in enumerate(outputs):
            sens_matrix[i, j] = abs(sensitivity[param][output])
    
    im = ax.imshow(sens_matrix, cmap='RdYlBu_r', aspect='auto')
    ax.set_xticks(range(len(outputs)))
    ax.set_xticklabels(outputs, rotation=45)
    ax.set_yticks(range(len(params)))
    ax.set_yticklabels([p.replace('_', ' ').title() for p in params])
    ax.set_title('Parameter Sensitivity (|Correlation|)')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('|Correlation Coefficient|')
    
    # Plot 6: Feasibility analysis
    ax = axes[5]
    feasible_rate = statistics['feasibility']['success_rate']
    failure_rate = statistics['feasibility']['failure_rate']
    
    ax.pie([feasible_rate, failure_rate], 
           labels=[f'Feasible\n({feasible_rate:.1%})', f'Infeasible\n({failure_rate:.1%})'],
           colors=['lightgreen', 'lightcoral'],
           autopct='%1.1f%%')
    ax.set_title('Design Feasibility')
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    print("=== Monte Carlo Sensitivity Analysis ===")
    
    # Run analysis
    analysis = monte_carlo_coil_analysis(n_samples=1000)
    
    # Print key results
    print(f"\nFeasibility: {analysis['statistics']['feasibility']['success_rate']:.1%} of designs meet all criteria")
    print(f"Feasible samples: {analysis['statistics']['feasibility']['feasible_samples']}/{analysis['statistics']['feasibility']['total_samples']}")
    
    print(f"\nKey Performance Metrics (feasible designs only):")
    for metric in ['B_center', 'field_ripple', 'thermal_margin', 'hoop_stress']:
        stats = analysis['statistics'][metric]
        print(f"{metric.replace('_', ' ').title()}:")
        print(f"  Mean ± Std: {stats['mean']:.3f} ± {stats['std']:.3f}")
        print(f"  95% CI: [{stats['percentile_5']:.3f}, {stats['percentile_95']:.3f}]")
    
    print(f"\nTop Parameter Sensitivities:")
    # Find parameters with highest sensitivity to key outputs
    for output in ['B_center', 'hoop_stress']:
        sensitivities = [(param, abs(analysis['sensitivity'][param][output])) 
                        for param in analysis['sensitivity'].keys()]
        sensitivities.sort(key=lambda x: x[1], reverse=True)
        print(f"\n{output.replace('_', ' ').title()}:")
        for param, sens in sensitivities[:3]:
            print(f"  {param.replace('_', ' ').title()}: {sens:.3f}")
    
    # Generate plots
    fig = plot_sensitivity_analysis(analysis)
    fig.savefig('/home/echo_/Code/asciimath/hts-coils/artifacts/sensitivity_analysis.png', 
                dpi=300, bbox_inches='tight')
    print(f"\nSensitivity analysis plot saved to artifacts/sensitivity_analysis.png")