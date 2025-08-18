import numpy as np
mu_0 = 4e-7 * np.pi  # Permeability of free space [H/m]
from typing import Tuple


def hts_coil_field(r: np.ndarray, I: float = 5000.0, N: int = 100, R: float = 1.0) -> np.ndarray:
    """Compute B-field at a point r from a single circular HTS coil using a discretized
    Biot–Savart loop approch. Returns vector B (Tesla).

    Parameters
    - r: 3-vector position [x,y,z] (meters)
    - I: current per turn (A)
    - N: number of turns
    - R: coil radius (m)
    """
    r = np.asarray(r, dtype=float)
    theta = np.linspace(0.0, 2.0 * np.pi, 360, endpoint=False)
    dl = R * np.vstack([-np.sin(theta), np.cos(theta), np.zeros_like(theta)])
    seg_len = 2.0 * np.pi * R / len(theta)
    dl *= seg_len
    B = np.zeros(3, dtype=float)
    for i in range(len(theta)):
        rp = r - np.array([R * np.cos(theta[i]), R * np.sin(theta[i]), 0.0])
        rp_mag = np.linalg.norm(rp)
        if rp_mag <= 1e-9:
            continue
        B += (mu_0 / (4.0 * np.pi)) * (I * N) * np.cross(dl[:, i], rp) / (rp_mag ** 3)
    return B


def sample_circular_coil_plane(
    I: float = 5000.0, N: int = 100, R: float = 1.0, extent: float = 0.5, n: int = 101
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample Bz on the coil plane (z=0) over a square grid, return X, Y, Bz arrays.
    Used to calculate ripple statistics.
    """
    xs = np.linspace(-extent, extent, n)
    ys = np.linspace(-extent, extent, n)
    X, Y = np.meshgrid(xs, ys, indexing="xy")
    Bz = np.zeros_like(X)
    for i in range(n):
        for j in range(n):
            B = hts_coil_field(np.array([X[i, j], Y[i, j], 0.0]), I=I, N=N, R=R)
            Bz[i, j] = B[2]
    return X, Y, Bz

