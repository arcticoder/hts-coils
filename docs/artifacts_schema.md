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
- kpis: { B_mean_T, B_std_T, ripple_rms }
- assumptions: input args used

plots_manifest.json
- config_hash: string
- plots: [ { path: string, caption: string } ]

volumetric_kpis.json
- kpis: { B_mean_T, B_std_T, ripple_rms, coverage_fraction, stored_energy_J, hts_efficiency }
- assumptions: args
- config_hash: string

best_config.json
- geom: string
- N, I, R: numbers
- sep: number (helmholtz only)
- B_mean_T, B_std_T, ripple_rms: numbers at sampling ROI

Tolerance UQ (tolerance_uq.json)
- baseline: KPIs at nominal
- radius: [{ dR, KPIs }]
- axial: [{ dz, KPIs }]
