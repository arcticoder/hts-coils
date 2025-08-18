import numpy as np
mu_0 = 4e-7 * np.pi  # Permeability of free space [H/m]
from typing import Tuple, List, Sequence


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


def _loop_field_at(r: np.ndarray, I: float, N: int, R: float, z0: float = 0.0) -> np.ndarray:
    """Field of a circular loop centered at (0,0,z0)."""
    x, y, z = float(r[0]), float(r[1]), float(r[2])
    return hts_coil_field(np.array([x, y, z - z0]), I=I, N=N, R=R)


def field_from_loops(r: np.ndarray, loops: Sequence[Tuple[float, int, float, float]]) -> np.ndarray:
    """Sum field from multiple loops.
    loops: sequence of tuples (I, N, R, z0)
    """
    B = np.zeros(3, dtype=float)
    for I, N, R, z0 in loops:
        B += _loop_field_at(r, I=I, N=N, R=R, z0=z0)
    return B


def sample_plane_from_loops(
    loops: Sequence[Tuple[float, int, float, float]], extent: float = 0.5, n: int = 101, z_plane: float = 0.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    xs = np.linspace(-extent, extent, n)
    ys = np.linspace(-extent, extent, n)
    X, Y = np.meshgrid(xs, ys, indexing="xy")
    Bz = np.zeros_like(X)
    for i in range(n):
        for j in range(n):
            B = field_from_loops(np.array([X[i, j], Y[i, j], z_plane]), loops)
            Bz[i, j] = B[2]
    return X, Y, Bz


def sample_helmholtz_pair_plane(
    I: float, N: int, R: float, separation: float | None = None, extent: float = 0.5, n: int = 101
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample Bz on the plane z=0 for a Helmholtz pair (two identical coaxial loops).
    By default, Helmholtz separation = R.
    """
    if separation is None:
        separation = R
    z = separation / 2.0
    loops = [(I, N, R, -z), (I, N, R, +z)]
    return sample_plane_from_loops(loops, extent=extent, n=n, z_plane=0.0)


def sample_stack_plane(
    I: float, N: int, R: float, layers: int, axial_spacing: float, extent: float = 0.5, n: int = 101
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample Bz for a stack of identical loops equally spaced along z with given spacing.
    Centered around z=0.
    """
    offsets = np.linspace(-(layers - 1) / 2.0, (layers - 1) / 2.0, layers) * axial_spacing
    loops = [(I, N, R, float(z0)) for z0 in offsets]
    return sample_plane_from_loops(loops, extent=extent, n=n, z_plane=0.0)


def sample_volume_from_loops(
    loops: Sequence[Tuple[float, int, float, float]],
    extent: float = 0.2,
    n: int = 41,
    z_extent: float = 0.2,
    nz: int = 21,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sample |B| on a 3D grid centered at origin; returns X, Y, Z, Bmag arrays.
    Useful for volumetric KPIs.
    """
    xs = np.linspace(-extent, extent, n)
    ys = np.linspace(-extent, extent, n)
    zs = np.linspace(-z_extent, z_extent, nz)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="xy")
    Bmag = np.zeros_like(X)
    for ix in range(n):
        for iy in range(n):
            for iz in range(nz):
                B = field_from_loops(np.array([X[ix, iy, iz], Y[ix, iy, iz], Z[ix, iy, iz]]), loops)
                Bmag[ix, iy, iz] = np.linalg.norm(B)
    return X, Y, Z, Bmag


def smear_loop_average(
    I: float,
    N: int,
    R: float,
    width: float = 0.0,
    thickness: float = 0.0,
    samples: int = 3,
    shape: str = "rect",
    cs_radius: float = 0.0,
) -> List[Tuple[float, int, float, float]]:
    """Return a list of sub-loops approximating a finite cross-section conductor.

    shape:
      - "rect": smear uniformly across radial width and axial thickness (default)
      - "round": smear within a circular cross-section of radius cs_radius in (dr, dz)
    """
    subloops: List[Tuple[float, int, float, float]] = []
    if shape == "round" and cs_radius > 0.0:
        # Sample a disk in (dr, dz)
        n = max(1, samples)
        # Polar grid samples
        rs = np.linspace(0.0, cs_radius, n)
        phis = np.linspace(0.0, 2.0 * np.pi, n, endpoint=False)
        pts = []
        for r_ in rs:
            for phi in phis:
                dr = r_ * np.cos(phi)
                dz = r_ * np.sin(phi)
                pts.append((dr, dz))
        if not pts:
            return [(I, N, R, 0.0)]
        w = 1.0 / len(pts)
        for dr, dz in pts:
            subloops.append((I * w, N, float(R + dr), float(dz)))
        return subloops

    # Default rectangular smear
    if width <= 0.0 and thickness <= 0.0:
        return [(I, N, R, 0.0)]
    radii = np.linspace(max(1e-6, R - width / 2.0), R + width / 2.0, max(1, samples))
    zoffs = np.linspace(-thickness / 2.0, thickness / 2.0, max(1, samples))
    w = 1.0 / (len(radii) * len(zoffs))
    for r in radii:
        for z0 in zoffs:
            subloops.append((I * w, N, float(r), float(z0)))
    return subloops


def helmholtz_loops(I: float, N: int, R: float, separation: float | None = None) -> List[Tuple[float, int, float, float]]:
    """Construct loop list for a Helmholtz pair centered at origin."""
    s = R if separation is None else float(separation)
    z = s / 2.0
    return [(I, N, R, -z), (I, N, R, +z)]


def stack_layers_loops(
    I: float,
    N: int,
    R: float,
    layers: int,
    axial_spacing: float,
    delta_R: float = 0.0,
) -> List[Tuple[float, int, float, float]]:
    """Construct loop list for a stacked multi-layer conductor geometry.
    Each layer i has radius R + (i - (layers-1)/2)*delta_R and z-offset per axial_spacing.
    """
    offsets = np.linspace(-(layers - 1) / 2.0, (layers - 1) / 2.0, layers)
    loops: List[Tuple[float, int, float, float]] = []
    for idx, u in enumerate(offsets):
        z0 = float(u * axial_spacing)
        r_i = float(R + u * delta_R)
        loops.append((I, N, r_i, z0))
    return loops

