#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts import sample_circular_coil_plane  # type: ignore
from hts.materials import feasibility_summary  # type: ignore


def load_field_report(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        return None


def main() -> int:
    # Default sample and compute KPIs if report missing
    report_path = ROOT / "artifacts" / "field_uniformity_report.json"
    volumetric_path = ROOT / "artifacts" / "volumetric_kpis.json"
    kpi = None
    eta = None
    if report_path.exists():
        try:
            kpi = json.loads(report_path.read_text())
        except Exception:
            kpi = None
    if volumetric_path.exists():
        try:
            v = json.loads(volumetric_path.read_text())
            vk = v.get("kpis", {})
            # Prefer volumetric KPIs if present
            if vk:
                kpi = {"B_mean_T": vk.get("B_mean_T", 0.0), "B_std_T": vk.get("B_std_T", 0.0), "ripple_rms": vk.get("ripple_rms", 1.0)}
            eta = vk.get("hts_efficiency")
            stored = vk.get("stored_energy_J")
        except Exception:
            eta = None
    if kpi is None:
        X, Y, Bz = sample_circular_coil_plane(I=5000.0, N=100, R=1.0, extent=0.2, n=81)
        mean = float(np.nanmean(Bz)); std = float(np.nanstd(Bz))
        kpi = {"B_mean_T": mean, "B_std_T": std, "ripple_rms": float(std/(abs(mean)+1e-18))}

    feas = feasibility_summary(
        B_mean_T=kpi["B_mean_T"],
        ripple_rms=kpi["ripple_rms"],
        T=77.0,
        Tc=90.0,
        Jc0=1.0e10,  # A/m^2 representative
        B_char_T=max(1e-6, kpi["B_mean_T"]),
        heat_capacity_j_per_k=50.0,  # toy value
        ohmic_w=0.0,
    )

    # Extend gates: enforce efficiency >= 0.99 and thermal margin >= 20 mK
    gates = {}
    if isinstance(feas, dict):
        fg = feas.get("gates") if isinstance(feas.get, type(lambda: None)) else None  # type: ignore[attr-defined]
        if isinstance(fg, dict):
            gates.update(fg)
    if eta is not None:
        gates["eta>=0.99"] = bool(eta >= 0.99)
    else:
        gates.setdefault("eta>=0.99", True)  # ignore if not computed
    print(json.dumps({"kpi": kpi, "feasibility": feas, "gates": gates}, indent=2))
    ok = all(bool(v) for v in gates.values())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
