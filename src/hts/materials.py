from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Dict

# Simplified Ginzburg–Landau style temperature dependence for J_c(T)
# J_c(T) = J_c0 * (1 - T/Tc)^(3/2)
def jc_vs_temperature(T: float, Tc: float, Jc0: float) -> float:
    if Tc <= 0:
        raise ValueError("Tc must be > 0")
    x = max(0.0, 1.0 - T / Tc)
    return Jc0 * (x ** 1.5)


# Very simple magnetic-field derating model: J_c(T,B) = J_c(T) / (1 + (B/B0)^n)
def jc_vs_tb(T: float, B: float, Tc: float, Jc0: float, B0: float = 5.0, n: float = 1.5) -> float:
    base = jc_vs_temperature(T, Tc, Jc0)
    if B <= 0:
        return base
    return base / (1.0 + (B / max(1e-12, B0)) ** max(0.0, n))


@dataclass
class ThermalConfig:
    Tc: float = 90.0        # K (REBCO > 77K typical)
    T_op: float = 77.0      # K
    heat_margin_mk: float = 20.0  # mK minimum desired margin


def thermal_margin_estimate(power_w: float, heat_capacity_j_per_k: float) -> float:
    """Return approximate temperature rise (K) given power and lumped heat capacity.
    This is a toy model used to gate obviously unsafe conditions.
    """
    if heat_capacity_j_per_k <= 0:
        return math.inf
    return power_w / heat_capacity_j_per_k


def enhanced_thermal_simulation(I: float, T_base: float = 20.0, Q_rad: float = 1e-3,
                               conductor_length: float = 100.0, tape_width: float = 4e-3,
                               cryo_efficiency: float = 0.1, P_cryo: float = 100.0,
                               T_env: float = 300.0, emissivity: float = 0.1,
                               stefan_boltzmann: float = 5.67e-8) -> Dict[str, float]:
    """
    Enhanced thermal simulation for space conditions including cryocooler and MLI effects.
    
    Args:
        I: Current (A) - not used for HTS below Tc
        T_base: Base operating temperature (K)
        Q_rad: External radiant heat load (W)
        conductor_length: Total conductor length (m)
        tape_width: HTS tape width (m)
        cryo_efficiency: Cryocooler efficiency (COP)
        P_cryo: Cryocooler electrical power (W)
        T_env: Environment temperature (K) for space (300K sunlit)
        emissivity: Tape surface emissivity
        stefan_boltzmann: Stefan-Boltzmann constant (W/m²/K⁴)
        
    Returns:
        Dict with enhanced thermal analysis
    """
    # HTS tape surface area for radiation
    A_rad = conductor_length * tape_width  # m²
    
    # Multi-layer insulation (MLI) heat leak - simplified model
    Q_mli = 1e-4 * A_rad  # ~0.1 mW/cm² typical for good MLI
    
    # Radiation heat input from environment (space) - with thermal shielding
    # In practice, HTS coils would be inside a cryostat with radiation shields
    # Assume effective shield temperature ~100K instead of 300K
    T_shield = 100.0  # K - intermediate shield temperature
    Q_rad_env = emissivity * stefan_boltzmann * A_rad * (T_shield**4 - T_base**4)
    
    # Total heat load
    Q_total = Q_rad + Q_mli + max(0, Q_rad_env)  # W
    
    # Cryocooler cooling capacity
    Q_cryo_capacity = cryo_efficiency * P_cryo  # W of cooling
    
    # Net heat to be radiated away by tape
    Q_net = Q_total - Q_cryo_capacity
    
    if Q_net > 0:
        # Need to radiate Q_net, solve: Q_net = σ*A*ε*(T⁴ - T_env⁴) 
        # For small ΔT: Q_net ≈ 4*σ*A*ε*T_base³*ΔT
        delta_T = Q_net / (4 * stefan_boltzmann * A_rad * emissivity * T_base**3)
    else:
        # Cryocooler can handle the load
        delta_T = 0.0
    
    T_final = T_base + delta_T
    
    return {
        'T_base': T_base,
        'T_final': T_final,
        'delta_T': delta_T,
        'Q_total': Q_total,
        'Q_rad_external': Q_rad,
        'Q_mli': Q_mli, 
        'Q_rad_env': max(0, Q_rad_env),
        'Q_cryo_capacity': Q_cryo_capacity,
        'Q_net': Q_net,
        'A_rad': A_rad,
        'thermal_margin_K': max(0, 90.0 - T_final),  # Assume Tc=90K
        'cryo_sufficient': Q_net <= 0
    }


def feasibility_summary(
    B_mean_T: float,
    ripple_rms: float,
    T: float,
    Tc: float,
    Jc0: float,
    B_char_T: float,
    heat_capacity_j_per_k: float,
    ohmic_w: float = 0.0,
    conductor_length: float = 100.0,
) -> Dict[str, object]:
    """Generate a simple feasibility summary consistent with goals:
    - B_mean >= 5 T
    - ripple_rms <= 0.01 (<=1%)
    - Thermal margin >= 20 mK
    - J_c(T,B) > 0 (not quenching by model)
    """
    jm = jc_vs_tb(T=T, B=B_char_T, Tc=Tc, Jc0=Jc0)
    
    # Use enhanced thermal simulation instead of simple estimate
    thermal_result = enhanced_thermal_simulation(
        I=0.0,  # Current doesn't matter for resistanceless HTS
        T_base=T,
        Q_rad=ohmic_w,  # Use ohmic_w as external heat load
        conductor_length=conductor_length
    )
    
    thermal_margin_mk = thermal_result['thermal_margin_K'] * 1000.0  # Convert to mK
    
    gates = {
        "B_mean>=5T": B_mean_T >= 5.0,
        "ripple<=0.01": ripple_rms <= 0.01,
        "thermal_margin>=20mK": thermal_margin_mk >= 20.0,
        "Jc_positive": jm > 0.0,
    }
    return {
        "inputs": {
            "B_mean_T": B_mean_T,
            "ripple_rms": ripple_rms,
            "T": T,
            "Tc": Tc,
            "Jc0": Jc0,
            "B_char_T": B_char_T,
            "ohmic_w": ohmic_w,
            "heat_capacity_j_per_k": heat_capacity_j_per_k,
            "conductor_length": conductor_length,
        },
        "derived": {
            "Jc_T_B": jm,
            "thermal_margin_mk": thermal_margin_mk,
            "thermal_simulation": thermal_result,
        },
        "gates": gates,
    }
