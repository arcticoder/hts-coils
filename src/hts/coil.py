import numpy as np
mu_0 = 4e-7 * np.pi

def biot_savart_loop(r: np.ndarray, I: float, R: float, segments: int = 360) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    theta = np.linspace(0.0, 2.0*np.pi, segments, endpoint=False)
    dl = R * np.vstack([-np.sin(theta), np.cos(theta), np.zeros_like(theta)])
    seg_len = 2.0 * np.pi * R / segments
    dl *= seg_len
    B = np.zeros(3, dtype=float)
    for i in range(segments):
        rp = r - np.array([R*np.cos(theta[i]), R*np.sin(theta[i]), 0.0])
        d = np.linalg.norm(rp)
        if d <= 1e-9:
            continue
        B += (mu_0/(4*np.pi)) * np.cross(dl[:, i], rp) / (d**3)
    return B

def loop_stack_Bz_plane(I: float, N: int, R: float, extent: float = 0.2, n: int = 81):
    xs = np.linspace(-extent, extent, n)
    ys = np.linspace(-extent, extent, n)
    X, Y = np.meshgrid(xs, ys, indexing="xy")
    Bz = np.zeros_like(X)
    for i in range(n):
        for j in range(n):
            B = np.zeros(3)
            for k in range(N):
                B += biot_savart_loop(np.array([X[i, j], Y[i, j], 0.0]), I=I, R=R)
            Bz[i, j] = B[2]
    return X, Y, Bz

def kpis_from_B(B: np.ndarray) -> dict:
    mean = float(np.nanmean(B))
    std = float(np.nanstd(B))
    ripple = float(std / (abs(mean) + 1e-18))
    return {"B_mean_T": mean, "B_std_T": std, "ripple_rms": ripple}
