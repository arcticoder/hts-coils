#!/usr/bin/env python3
"""
AC loss modeling for REBCO HTS coils during ramping and dynamic operation.

Implements Norris and Brandt models for hysteresis and eddy current losses
in superconducting tapes under time-varying magnetic fields.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt


def norris_hysteresis_loss(I_op: float, I_c: float, f: float, width: float = 4e-3) -> float:
    """
    Calculate AC hysteresis loss using Norris model for REBCO tape.
    
    Args:
        I_op: Operating current [A]
        I_c: Critical current [A] 
        f: Frequency [Hz]
        width: Tape width [m]
        
    Returns:
        AC loss per unit length [W/m]
    """
    mu0 = 4e-7 * np.pi
    
    # Normalized current
    i = I_op / I_c
    
    if i <= 1.0:
        # Subcritical regime
        if i <= 0.5:
            # Low current approximation
            P_ac = (2 * mu0 * I_c**2 * f * i**3) / (3 * np.pi * width)
        else:
            # Norris exact formula for i > 0.5
            P_ac = (mu0 * I_c**2 * f) / (np.pi * width) * (i * (1 - 2*i/3) + np.log(2*i) - 1 + 2/3)
    else:
        # Overcritical regime - flux flow losses dominate
        rho_ff = 1e-8  # Flux flow resistivity [Ω⋅m]
        thickness = 1e-6  # REBCO layer thickness [m]
        P_ac = rho_ff * (I_op - I_c)**2 / (width * thickness)
        
    return P_ac


def brandt_field_sweep_loss(B_ext: float, dB_dt: float, width: float = 4e-3, 
                           thickness: float = 1e-6, Jc: float = 3e8) -> float:
    """
    Calculate AC loss due to external field sweep using Brandt model.
    
    Args:
        B_ext: External magnetic field [T]
        dB_dt: Field ramp rate [T/s]
        width: Tape width [m]
        thickness: REBCO thickness [m]
        Jc: Critical current density [A/m²]
        
    Returns:
        AC loss per unit length [W/m]
    """
    if abs(dB_dt) < 1e-12:  # Handle static case
        return 0.0
        
    mu0 = 4e-7 * np.pi
    
    # Penetration field
    B_p = mu0 * Jc * thickness
    
    # Field amplitude for sinusoidal variation
    B_a = abs(dB_dt) / (2 * np.pi * 1.0)  # Assume 1 Hz equivalent
    
    if B_a <= B_p:
        # Partial penetration
        P_ac = (4 * mu0 * Jc * width * thickness / (3 * np.pi)) * (B_a / B_p)**3
    else:
        # Full penetration
        P_ac = (mu0 * Jc * width * thickness / np.pi) * B_a * (1 - B_p / (3 * B_a))
        
    return P_ac * abs(dB_dt) / max(B_a, 1e-12)  # Avoid division by zero


def total_ac_loss(I_op: float, I_c: float, B_ext: float, f: float = 0.01, 
                  dB_dt: float = 0.1, coil_length: float = 20100) -> Dict[str, float]:
    """
    Calculate total AC losses for HTS coil including transport and field sweep components.
    
    Args:
        I_op: Operating current [A]
        I_c: Critical current [A]
        B_ext: External magnetic field [T]
        f: Transport current frequency [Hz]
        dB_dt: Field ramp rate [T/s]
        coil_length: Total conductor length [m]
        
    Returns:
        Dictionary with loss components and thermal implications
    """
    # Transport current losses (Norris model)
    P_transport = norris_hysteresis_loss(I_op, I_c, f)
    
    # Field sweep losses (Brandt model)
    P_field = brandt_field_sweep_loss(B_ext, dB_dt)
    
    # Total losses per unit length
    P_per_meter = P_transport + P_field
    
    # Total coil losses
    P_total = P_per_meter * coil_length
    
    # Thermal impact analysis
    thermal_margin_loss = P_total / 0.5  # Assume 0.5 W/K cooling capacity
    
    results = {
        'transport_loss_W_per_m': P_transport,
        'field_sweep_loss_W_per_m': P_field,
        'total_loss_per_m_W': P_per_meter,
        'total_coil_loss_W': P_total,
        'thermal_margin_reduction_K': thermal_margin_loss,
        'compatible_with_70K_margin': thermal_margin_loss < 10.0  # Conservative limit
    }
    
    return results


def ac_loss_scaling_analysis():
    """
    Analyze AC loss scaling with operating parameters for design optimization.
    """
    # Parameter ranges for analysis
    current_ratios = np.linspace(0.1, 0.9, 20)  # I_op/I_c
    frequencies = np.logspace(-3, 0, 20)  # 1 mHz to 1 Hz
    ramp_rates = np.logspace(-2, 1, 20)  # 0.01 to 10 T/s
    
    # Fixed parameters
    I_c = 23420  # Critical current for current design [A]
    B_ext = 2.1  # Operating field [T]
    
    results = {}
    
    # Current ratio dependence
    results['current_scaling'] = []
    for i_ratio in current_ratios:
        I_op = i_ratio * I_c
        loss_data = total_ac_loss(I_op, I_c, B_ext)
        results['current_scaling'].append({
            'current_ratio': i_ratio,
            'total_loss_W': loss_data['total_coil_loss_W'],
            'thermal_compatible': loss_data['compatible_with_70K_margin']
        })
    
    # Frequency dependence
    results['frequency_scaling'] = []
    for f in frequencies:
        I_op = 0.5 * I_c  # 50% of critical current
        loss_data = total_ac_loss(I_op, I_c, B_ext, f=f)
        results['frequency_scaling'].append({
            'frequency_Hz': f,
            'total_loss_W': loss_data['total_coil_loss_W'],
            'transport_loss_W': loss_data['transport_loss_W_per_m'] * 20100
        })
    
    # Ramp rate dependence
    results['ramp_scaling'] = []
    for dB_dt in ramp_rates:
        I_op = 0.5 * I_c
        loss_data = total_ac_loss(I_op, I_c, B_ext, dB_dt=dB_dt)
        results['ramp_scaling'].append({
            'ramp_rate_T_per_s': dB_dt,
            'total_loss_W': loss_data['total_coil_loss_W'],
            'field_loss_W': loss_data['field_sweep_loss_W_per_m'] * 20100
        })
    
    return results


def plot_ac_loss_analysis():
    """
    Generate comprehensive AC loss analysis plots.
    """
    analysis = ac_loss_scaling_analysis()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Current ratio dependence
    current_data = analysis['current_scaling']
    i_ratios = [d['current_ratio'] for d in current_data]
    losses = [d['total_loss_W'] for d in current_data]
    
    ax1.semilogy(i_ratios, losses, 'b-', linewidth=2)
    ax1.set_xlabel('Current Ratio (I_op/I_c)')
    ax1.set_ylabel('Total AC Loss [W]')
    ax1.set_title('AC Loss vs Operating Current')
    ax1.grid(True, alpha=0.3)
    
    # Mark thermal limit
    thermal_limit = 10.0  # Conservative 10W thermal budget
    ax1.axhline(y=thermal_limit, color='r', linestyle='--', label=f'Thermal Limit ({thermal_limit}W)')
    ax1.legend()
    
    # Plot 2: Frequency dependence
    freq_data = analysis['frequency_scaling']
    freqs = [d['frequency_Hz'] for d in freq_data]
    transport_losses = [d['transport_loss_W'] for d in freq_data]
    
    ax2.loglog(freqs, transport_losses, 'g-', linewidth=2)
    ax2.set_xlabel('Frequency [Hz]')
    ax2.set_ylabel('Transport AC Loss [W]')
    ax2.set_title('AC Loss vs Frequency')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Ramp rate dependence
    ramp_data = analysis['ramp_scaling']
    ramps = [d['ramp_rate_T_per_s'] for d in ramp_data]
    field_losses = [d['field_loss_W'] for d in ramp_data]
    
    ax3.loglog(ramps, field_losses, 'orange', linewidth=2)
    ax3.set_xlabel('Ramp Rate [T/s]')
    ax3.set_ylabel('Field Sweep Loss [W]')
    ax3.set_title('AC Loss vs Field Ramp Rate')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Combined loss budget
    # Show operating envelope
    I_op_nominal = 1171  # Nominal operating current
    I_c_nominal = 23420  # Critical current
    current_ratio = I_op_nominal / I_c_nominal
    
    # Calculate losses for typical operating scenarios
    scenarios = {
        'Static Hold': total_ac_loss(I_op_nominal, I_c_nominal, 2.1, f=0, dB_dt=0),
        'Slow Ramp (0.01 T/s)': total_ac_loss(I_op_nominal, I_c_nominal, 2.1, f=0, dB_dt=0.01),
        'Fast Ramp (0.1 T/s)': total_ac_loss(I_op_nominal, I_c_nominal, 2.1, f=0, dB_dt=0.1),
        'AC Ripple (1 mHz)': total_ac_loss(I_op_nominal, I_c_nominal, 2.1, f=0.001, dB_dt=0)
    }
    
    scenario_names = list(scenarios.keys())
    scenario_losses = [scenarios[name]['total_coil_loss_W'] for name in scenario_names]
    colors = ['blue', 'green', 'orange', 'red']
    
    bars = ax4.bar(scenario_names, scenario_losses, color=colors, alpha=0.7)
    ax4.axhline(y=thermal_limit, color='r', linestyle='--', linewidth=2, label=f'Thermal Budget ({thermal_limit}W)')
    ax4.set_ylabel('Total AC Loss [W]')
    ax4.set_title('Operating Scenario Loss Budget')
    ax4.legend()
    ax4.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar, loss in zip(bars, scenario_losses):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.05,
                f'{loss:.2f}W', ha='center', va='bottom')
    
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    print("=== HTS Coil AC Loss Analysis ===")
    
    # Analyze nominal operating conditions
    I_op = 1171  # Operating current [A]
    I_c = 23420  # Critical current for 20 tapes at 2.1T [A]
    B_ext = 2.1  # Field [T]
    
    # Typical operating scenarios
    scenarios = [
        ("Static Operation", {"f": 0, "dB_dt": 0}),
        ("Slow Ramp (0.01 T/s)", {"f": 0, "dB_dt": 0.01}),
        ("Fast Ramp (0.1 T/s)", {"f": 0, "dB_dt": 0.1}),
        ("AC Ripple (1 mHz)", {"f": 0.001, "dB_dt": 0})
    ]
    
    print(f"\nOperating Point: I_op = {I_op} A, I_c = {I_c} A, B = {B_ext} T")
    print(f"Current Ratio: {I_op/I_c:.3f}")
    
    for name, params in scenarios:
        result = total_ac_loss(I_op, I_c, B_ext, **params)
        print(f"\n{name}:")
        print(f"  Transport Loss: {result['transport_loss_W_per_m']*1000:.3f} mW/m")
        print(f"  Field Sweep Loss: {result['field_sweep_loss_W_per_m']*1000:.3f} mW/m")
        print(f"  Total Coil Loss: {result['total_coil_loss_W']:.3f} W")
        print(f"  Thermal Impact: {result['thermal_margin_reduction_K']:.1f} K")
        print(f"  Compatible with 70K margin: {result['compatible_with_70K_margin']}")
    
    # Generate analysis plots
    fig = plot_ac_loss_analysis()
    fig.savefig('/home/echo_/Code/asciimath/hts-coils/artifacts/ac_loss_analysis.png', 
                dpi=300, bbox_inches='tight')
    print(f"\nAC loss analysis plot saved to artifacts/ac_loss_analysis.png")