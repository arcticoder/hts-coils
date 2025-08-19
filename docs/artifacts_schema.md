# Artifacts Schema

This document describes the JSON and CSV schemas emitted by scripts.

sweep_results.csv
- geom: string (single|helmholtz|stack)
- N: int (turns)
- I: float (A)
- R: float (m)
- sep: float (m, only for helmholtz)
- layers: int (stack only)
- dz: float (m, stack only)
- B_mean_T: float
- B_std_T: float
- ripple_rms: float
- field_per_A_turn: float (Tesla per A-turn)
- energy_per_T: float (J/T)

sweep_topk.json
- config_hash: string
- rows: array of objects from sweep_results.csv subset

volumetric_kpis.json
- kpis: { B_mean_T, B_std_T, ripple_rms, coverage_fraction, stored_energy_J, hts_efficiency }
- assumptions: input args used (I,N,R,width,thickness,shape,cs_radius,layers,delta_R,extent,n,z_extent,nz,uniformity_pct,R_circ,duration)
- config_hash: string

plots_manifest.json
- config_hash: string
- plots: [ { path: string, caption: string } ]

Notes
- Stored energy U is computed via grid integration of |B|: U ≈ Σ B^2 /(2 μ0) ΔV.
- Efficiency η = U / (U + I² R Δt) assuming small residual resistance R over time window Δt.

feasibility_gates_report.json (printed by metrics_gate)
- kpi: { B_mean_T, B_std_T, ripple_rms }
- feasibility: outputs from materials.feasibility_summary
- gates: includes base gates and, if available, eta>=0.99

best_config.json
- geom: string
- N, I, R: numbers
- sep: number (helmholtz only)
- B_mean_T, B_std_T, ripple_rms: numbers at sampling ROI

Tolerance UQ (tolerance_uq.json)
- baseline: KPIs at nominal
- radius: [{ dR, KPIs }]
- axial: [{ dz, KPIs }]
