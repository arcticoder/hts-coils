#!/usr/bin/env python3
"""
Mechanical reinforcement analysis for HTS coils to mitigate hoop stress delamination risk.

Implements strategies to reduce hoop stress below the 35 MPa REBCO delamination limit
through structural reinforcement and optimized conductor stacking.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt


def calculate_hoop_stress(B_field: float, radius: float, thickness: float) -> float:
    """
    Calculate hoop stress in cylindrical conductor.
    
    Args:
        B_field: Magnetic field strength [T]
        radius: Coil radius [m]  
        thickness: Conductor thickness [m]
        
    Returns:
        Hoop stress [MPa]
    """
    mu0 = 4e-7 * np.pi  # H/m
    sigma_hoop = (B_field**2 * radius) / (2 * mu0 * thickness) / 1e6  # Convert to MPa
    return sigma_hoop


def mitigate_hoop_stress(B=2.1, R=0.2, thickness=0.002, delam_limit=35.0):
    """
    Calculate mechanical reinforcement needed to reduce hoop stress below delamination limit.
    
    Args:
        B: Magnetic field [T]
        R: Coil radius [m]
        thickness: Initial conductor thickness [m]
        delam_limit: REBCO delamination limit [MPa]
        
    Returns:
        Dict with mitigation strategies and parameters
    """
    initial_stress = calculate_hoop_stress(B, R, thickness)
    
    results = {
        'initial_stress_MPa': initial_stress,
        'delamination_limit_MPa': delam_limit,
        'safety_factor': delam_limit / initial_stress if initial_stress > 0 else float('inf'),
        'mitigation_required': initial_stress > delam_limit
    }
    
    if initial_stress > delam_limit:
        # Strategy 1: Increase conductor thickness
        required_thickness = thickness * initial_stress / delam_limit
        results['thickness_mitigation'] = {
            'new_thickness_mm': required_thickness * 1000,
            'thickness_increase_factor': required_thickness / thickness,
            'additional_tapes': int(np.ceil(required_thickness / 0.0001))  # 0.1mm per tape
        }
        
        # Strategy 2: Steel bobbin reinforcement
        # Composite stress: σ_composite = σ_hts * (E_hts * t_hts) / (E_hts * t_hts + E_steel * t_steel)
        E_rebco = 150e9  # Pa, REBCO modulus
        E_steel = 200e9  # Pa, stainless steel modulus
        
        # Find steel thickness to reduce stress to target
        target_stress = delam_limit * 0.8  # 20% safety margin
        steel_thickness = thickness * E_rebco * (initial_stress - target_stress) / (target_stress * E_steel)
        
        results['bobbin_reinforcement'] = {
            'steel_thickness_mm': steel_thickness * 1000,
            'steel_mass_kg_per_turn': 2 * np.pi * R * steel_thickness * 7800,  # Steel density
            'composite_stress_MPa': target_stress,
            'reinforcement_factor': initial_stress / target_stress
        }
        
        # Strategy 3: Distributed support structure
        # Use Kapton/G10 spacers between tape layers
        results['distributed_support'] = {
            'spacer_thickness_mm': 0.05,  # 50 μm Kapton
            'spacers_per_turn': int(np.ceil(required_thickness / 0.0001 / 5)),  # Every 5 tapes
            'stress_reduction_factor': 0.7  # Empirical from literature
        }
        
    else:
        results['status'] = 'Design within delamination limits'
        
    return results


def design_reinforced_coil(N=400, I=1171, R=0.2, B_target=2.1):
    """
    Design mechanically reinforced HTS coil configuration.
    
    Returns optimized design with reinforcement specifications.
    """
    tape_thickness = 0.0001  # 0.1mm REBCO tape
    initial_stack = 20 * tape_thickness  # 20 tapes per turn
    
    # Calculate reinforcement needs
    mitigation = mitigate_hoop_stress(B_target, R, initial_stack)
    
    design = {
        'baseline': {
            'turns': N,
            'current_A': I,
            'radius_m': R,
            'field_T': B_target,
            'tape_stack_mm': initial_stack * 1000,
            'hoop_stress_MPa': mitigation['initial_stress_MPa']
        }
    }
    
    if mitigation['mitigation_required']:
        # Implement combined reinforcement strategy
        reinforced_thickness = mitigation['thickness_mitigation']['new_thickness_mm'] / 1000
        steel_thickness = mitigation['bobbin_reinforcement']['steel_thickness_mm'] / 1000
        
        design['reinforced'] = {
            'conductor_stack_mm': reinforced_thickness * 1000,
            'total_tapes': mitigation['thickness_mitigation']['additional_tapes'],
            'steel_bobbin_thickness_mm': steel_thickness * 1000,
            'steel_mass_per_coil_kg': N * mitigation['bobbin_reinforcement']['steel_mass_kg_per_turn'],
            'final_hoop_stress_MPa': mitigation['bobbin_reinforcement']['composite_stress_MPa'],
            'safety_margin': mitigation['bobbin_reinforcement']['reinforcement_factor'],
            'cost_increase_factor': mitigation['thickness_mitigation']['thickness_increase_factor']
        }
        
        # Update prototype specifications
        additional_tape_km = (mitigation['thickness_mitigation']['thickness_increase_factor'] - 1) * 20.1
        steel_cost = design['reinforced']['steel_mass_per_coil_kg'] * 2 * 5  # $5/kg steel, 2 coils
        
        design['prototype_impact'] = {
            'additional_rebco_tape_km': additional_tape_km,
            'steel_cost_USD': steel_cost,
            'total_cost_increase_USD': additional_tape_km * 20000 + steel_cost  # $20k/km tape + steel
        }
        
    return design


def plot_stress_mitigation_strategies(B_range=np.linspace(1.0, 3.0, 20)):
    """
    Generate plots comparing stress mitigation strategies across field strengths.
    """
    R = 0.2  # Fixed radius
    base_thickness = 0.002  # Base conductor thickness
    
    strategies = {}
    
    for B in B_range:
        mitigation = mitigate_hoop_stress(B, R, base_thickness)
        strategies[B] = mitigation
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Plot 1: Stress vs Field
    fields = list(strategies.keys())
    stresses = [strategies[B]['initial_stress_MPa'] for B in fields]
    
    ax1.plot(fields, stresses, 'b-', linewidth=2, label='Baseline Design')
    ax1.axhline(y=35, color='r', linestyle='--', label='Delamination Limit')
    ax1.set_xlabel('Magnetic Field [T]')
    ax1.set_ylabel('Hoop Stress [MPa]')
    ax1.set_title('Hoop Stress vs Magnetic Field')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Reinforcement Requirements
    thickness_factors = [strategies[B]['thickness_mitigation']['thickness_increase_factor'] 
                        if strategies[B]['mitigation_required'] else 1.0 for B in fields]
    
    ax2.plot(fields, thickness_factors, 'g-', linewidth=2, label='Thickness Increase Factor')
    ax2.set_xlabel('Magnetic Field [T]')
    ax2.set_ylabel('Reinforcement Factor')
    ax2.set_title('Required Reinforcement vs Field')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    # Analyze current design
    print("=== HTS Coil Mechanical Reinforcement Analysis ===")
    
    # Current design parameters
    current_design = design_reinforced_coil()
    
    print("\nBaseline Design:")
    for key, value in current_design['baseline'].items():
        print(f"  {key}: {value}")
        
    if 'reinforced' in current_design:
        print("\nReinforced Design:")
        for key, value in current_design['reinforced'].items():
            print(f"  {key}: {value}")
            
        print("\nPrototype Cost Impact:")
        for key, value in current_design['prototype_impact'].items():
            print(f"  {key}: {value}")
    
    # Generate stress mitigation plot
    fig = plot_stress_mitigation_strategies()
    fig.savefig('/home/echo_/Code/asciimath/hts-coils/artifacts/stress_mitigation_analysis.png', 
                dpi=300, bbox_inches='tight')
    print("\nStress mitigation plot saved to artifacts/stress_mitigation_analysis.png")