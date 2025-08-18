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


def feasibility_summary(
    B_mean_T: float,
    ripple_rms: float,
    T: float,
    Tc: float,
    Jc0: float,
    B_char_T: float,
    heat_capacity_j_per_k: float,
    ohmic_w: float = 0.0,
) -> Dict[str, object]:
    """Generate a simple feasibility summary consistent with goals:
    - B_mean >= 5 T
    - ripple_rms <= 0.01 (<=1%)
    - Thermal margin >= 20 mK
    - J_c(T,B) > 0 (not quenching by model)
    """
    jm = jc_vs_tb(T=T, B=B_char_T, Tc=Tc, Jc0=Jc0)
    dT = thermal_margin_estimate(ohmic_w, heat_capacity_j_per_k)
    thermal_margin_mk = max(0.0, (0.02 - dT)) * 1000.0  # if > 0.02 K margin remain
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
        },
        "derived": {
            "Jc_T_B": jm,
            "thermal_margin_mk": thermal_margin_mk,
        },
        "gates": gates,
    }
