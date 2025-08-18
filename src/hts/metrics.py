from __future__ import annotations
import numpy as np
from typing import Sequence, Tuple
from .coil import mu_0, field_from_loops


def stored_magnetic_energy_uniform(B: np.ndarray, volume_m3: float) -> float:
    """Estimate stored magnetic energy U = ∫ B^2/(2μ0) dV using uniform approximation
    where B is representative magnitude and volume is given. For grid-based eval,
    use stored_magnetic_energy_grid.
    """
    return float((np.mean(B**2) / (2.0 * mu_0)) * volume_m3)


def stored_magnetic_energy_grid(B: np.ndarray, dx: float, dy: float, dz: float) -> float:
    """Estimate energy from a 3D grid of |B| values using Riemann sum.
    B can be either |B| or Bz; prefer |B|. Units: Tesla, meters.
    """
    dV = dx * dy * dz
    return float(np.sum((B ** 2) / (2.0 * mu_0)) * dV)


def field_per_A_turn(B_mean_T: float, N: int, I: float) -> float:
    """Metric: Tesla per A-turn."""
    if N * I == 0:
        return 0.0
    return float(B_mean_T / (N * I))


def energy_per_tesla(U_J: float, B_mean_T: float) -> float:
    """Joules per Tesla of mean field."""
    if B_mean_T <= 0:
        return float("inf")
    return float(U_J / B_mean_T)


def efficiency_hts_approx(U_J: float, I: float, R_circ_ohm: float = 0.0, duration_s: float = 1.0) -> float:
    """Define an energy efficiency for HTS as fraction of energy stored vs injected:
    η = U / (U + E_loss). With superconductors, R≈0, but include optional small R to
    reflect joint/resistive losses over a time window. Returns value in [0,1].
    """
    E_loss = (I**2) * R_circ_ohm * duration_s
    denom = U_J + E_loss
    return 1.0 if denom <= 0 else float(U_J / denom)


def center_field_from_loops(loops: Sequence[Tuple[float, int, float, float]]) -> float:
    """Compute |B| at origin from loop set."""
    B = field_from_loops(np.array([0.0, 0.0, 0.0]), loops)
    return float(np.linalg.norm(B))
