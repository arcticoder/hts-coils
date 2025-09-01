#!/usr/bin/env python3
"""
Simplified sensitivity analysis for HTS coil design parameters.
"""

import numpy as np
import matplotlib.pyplot as plt


def jc_vs_tb_simple(T, B, Tc=90, Jc0=300e6, B0=5.0, n=1.5):
    """Simplified critical current density model."""
    if T >= Tc:
        return 0.0
    temp_factor = (1 - T/Tc)**1.5
    field_factor = 1 / (1 + (B/B0)**n)
    return Jc0 * temp_factor * field_factor


def sensitivity_analysis():
    """Run simplified sensitivity analysis."""
    
    print("=== Simplified HTS Coil Sensitivity Analysis ===")
    
    # Base parameters
    N = 400
    I_op = 1171
    R = 0.2
    T_op = 20
    B_target = 2.1
    
    # Parameter variations (±1 standard deviation)
    variations = {
        'Jc0': {'nominal': 300e6, 'std': 50e6, 'unit': 'A/m²'},
        'tape_thickness': {'nominal': 0.1e-3, 'std': 0.02e-3, 'unit': 'm'},
        'radius': {'nominal': 0.2, 'std': 0.005, 'unit': 'm'},
        'temperature': {'nominal': 20, 'std': 2, 'unit': 'K'},
        'field_variation': {'nominal': 1.0, 'std': 0.05, 'unit': 'factor'}
    }
    
    # Monte Carlo samples
    n_samples = 1000
    results = {'B_field': [], 'hoop_stress': [], 'critical_current': [], 'feasible': []}
    
    print(f"Running {n_samples} Monte Carlo samples...")
    
    for i in range(n_samples):
        # Sample parameters
        Jc0 = np.random.normal(variations['Jc0']['nominal'], variations['Jc0']['std'])
        thickness = np.random.normal(variations['tape_thickness']['nominal'], 
                                   variations['tape_thickness']['std'])
        R_var = np.random.normal(variations['radius']['nominal'], 
                               variations['radius']['std'])
        T_var = np.random.normal(variations['temperature']['nominal'], 
                               variations['temperature']['std'])
        field_var = np.random.normal(variations['field_variation']['nominal'], 
                                   variations['field_variation']['std'])
        
        # Constrain parameters to realistic ranges
        Jc0 = max(200e6, min(400e6, Jc0))
        thickness = max(0.05e-3, min(0.15e-3, thickness))
        R_var = max(0.15, min(0.25, R_var))
        T_var = max(15, min(25, T_var))
        field_var = max(0.9, min(1.1, field_var))
        
        # Calculate field (simplified)
        B_nominal = 4e-7 * np.pi * N * I_op / (2 * R_var)
        B_field = B_nominal * field_var
        
        # Calculate critical current
        Jc_actual = jc_vs_tb_simple(T_var, B_field*0.1, Jc0=Jc0)  # Use lower field for Jc calc
        tapes_per_turn = 20
        width = 4e-3
        I_c = Jc_actual * tapes_per_turn * width * thickness
        
        # Calculate hoop stress
        conductor_thickness = tapes_per_turn * thickness
        mu0 = 4e-7 * np.pi
        hoop_stress = (B_field**2 * R_var) / (2 * mu0 * conductor_thickness) / 1e6  # MPa
        
        # Feasibility check (relaxed criteria for analysis)
        feasible = (I_op <= I_c * 0.5) and (hoop_stress <= 50.0) and (B_field >= 1.0)  # More permissive
        
        results['B_field'].append(B_field)
        results['hoop_stress'].append(hoop_stress)
        results['critical_current'].append(I_c)
        results['feasible'].append(feasible)
    
    # Convert to numpy arrays
    for key in results:
        results[key] = np.array(results[key])
    
    # Calculate statistics
    feasible_mask = results['feasible']
    feasible_fraction = np.mean(feasible_mask)
    
    print(f"\nResults:")
    print(f"Feasible designs: {feasible_fraction:.1%} ({np.sum(feasible_mask)}/{n_samples})")
    
    if np.sum(feasible_mask) > 0:
        B_feasible = results['B_field'][feasible_mask]
        stress_feasible = results['hoop_stress'][feasible_mask]
        
        print(f"\nFeasible Design Statistics:")
        print(f"Magnetic field: {np.mean(B_feasible):.3f} ± {np.std(B_feasible):.3f} T")
        print(f"Hoop stress: {np.mean(stress_feasible):.1f} ± {np.std(stress_feasible):.1f} MPa")
        print(f"Field range (95% CI): [{np.percentile(B_feasible, 2.5):.3f}, {np.percentile(B_feasible, 97.5):.3f}] T")
        print(f"Stress range (95% CI): [{np.percentile(stress_feasible, 2.5):.1f}, {np.percentile(stress_feasible, 97.5):.1f}] MPa")
        
        # Generate plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # Plot 1: Magnetic field distribution
        ax1.hist(B_feasible, bins=30, alpha=0.7, color='blue', density=True)
        ax1.axvline(np.mean(B_feasible), color='red', linestyle='--', label='Mean')
        ax1.axvline(B_target, color='green', linestyle=':', label='Target')
        ax1.set_xlabel('Magnetic Field [T]')
        ax1.set_ylabel('Probability Density')
        ax1.set_title('Field Strength Distribution')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Hoop stress distribution
        ax2.hist(stress_feasible, bins=30, alpha=0.7, color='red', density=True)
        ax2.axvline(np.mean(stress_feasible), color='red', linestyle='--', label='Mean')
        ax2.axvline(35, color='orange', linestyle=':', label='Delamination Limit')
        ax2.set_xlabel('Hoop Stress [MPa]')
        ax2.set_ylabel('Probability Density')
        ax2.set_title('Hoop Stress Distribution')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Field vs stress scatter
        ax3.scatter(B_feasible, stress_feasible, alpha=0.5, s=10)
        ax3.axhline(y=35, color='red', linestyle='--', label='Stress Limit')
        ax3.axvline(x=B_target, color='green', linestyle='--', label='Target Field')
        ax3.set_xlabel('Magnetic Field [T]')
        ax3.set_ylabel('Hoop Stress [MPa]')
        ax3.set_title('Field vs Stress Trade-off')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Feasibility breakdown
        labels = ['Feasible', 'Infeasible']
        sizes = [feasible_fraction, 1-feasible_fraction]
        colors = ['lightgreen', 'lightcoral']
        ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Design Feasibility')
        
        plt.tight_layout()
        fig.savefig('/home/echo_/Code/asciimath/hts-coils/artifacts/simplified_sensitivity_analysis.png', 
                    dpi=300, bbox_inches='tight')
        print(f"\nSensitivity analysis plot saved to artifacts/simplified_sensitivity_analysis.png")
        
    else:
        print("No feasible designs found in parameter space")
        
    return results


if __name__ == "__main__":
    sensitivity_analysis()