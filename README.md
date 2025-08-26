# HTS Coils — Research-stage objectives and prototype artifacts

Refined Objective (research-stage): Develop and evaluate HTS coil designs with target simulation and prototype metrics such as magnetic field strength in the 5–10 T range, low ripple, and thermal margins consistent with HTS operation at cryogenic conditions. Reported numeric values are model-derived or from limited prototype tests; they require independent validation and formal V&V prior to deployment.

Quickstart (CI-like local run):
- python scripts/generate_hts_artifacts.py  # writes artifacts/ and feasibility_gates_report.json

Optional extras:
- pip install -e .[opt]  # enables Bayesian optimizer (scikit-optimize)

Key equations (reference):
- Axial center field (single circular loop, N turns): B_center = μ0 N I / (2R)
- Ripple KPI: ripple_rms = std(B) / |mean(B)|
- Ginzburg–Landau J_c(T): J_c(T) = J_c0 (1 - T/T_c)^{3/2}

Code entry points:
- src/hts/coil.py — Biot–Savart discretized loop and sampling helpers
- src/hts/materials.py — J_c(T,B) and simple thermal margin utilities
- scripts/generate_hts_artifacts.py — grid sampling, KPIs, PNGs/JSON outputs
- scripts/analytic_axial_check.py — validates numeric vs analytic axial center field
- scripts/metrics_gate.py — enforces gates for B >= 5 T and ripple <= 1%

Docs:
- docs/roadmap.ndjson — milestones with math + python snippets
- docs/progress_log.ndjson — progress entries with parsable snippets
- docs/VnV-TODO.ndjson — validation tasks and snippet ideas (prioritize reproducible checks)
- docs/UQ-TODO.ndjson — uncertainty quantification tasks and snippet ideas (include sampling + sensitivity plans)

## Scope / Validation & Limitations

- **Research-stage status**: This repository contains simulation code, prototype scripts, and analysis notebooks. Reported metrics (e.g., field magnitude, ripple, efficiency) are either simulation outputs or derived from small-scale experiments; they are not validated for production use.
- **Uncertainty quantification**: For numeric claims, see `docs/UQ-TODO.ndjson` and any `artifacts/` outputs produced by `scripts/generate_hts_artifacts.py`. Where available, raw data, seed values, and environment details are included in `artifacts/` to reproduce reported results.
- **Recommended next steps**: Run the V&V tasks in `docs/VnV-TODO.ndjson` (unit tests, analytic checks, param sweeps) and produce CI-friendly reproducible artifacts (CSV/JSON + plotting scripts) that include confidence intervals or sensitivity sweeps.
- **Caveat**: Thermal margins, material J_c models, and efficiency calculations depend strongly on assumed material parameters, winding patterns, and boundary conditions; interpret reported numbers as illustrative, not prescriptive.

Additional features in this iteration:
- Sweep with caching keyed by config hash; new metrics (field per A-turn, energy per Tesla)
- Optimizer entry point (Bayesian via scikit-optimize if installed; fallback random search)
- Tolerance analysis for radius and axial misalignment
- Conductor cross-section smearing (rectangular and round presets)
- Plots: ripple histogram and centerline manifest
- Docs: howto_5T, artifacts schema

Energy and efficiency:
- Stored energy U computed by integrating |B|^2/(2 μ0) over a sampled 3D grid (scripts/volumetric_kpis.py).
- Approximate HTS efficiency η = U / (U + I² R Δt) with user-specified residual R and duration.

Make targets:
- make sweep — Helmholtz sweep with plots
- make volumetric — 3D KPIs (with smearing)
- make opt — optimize coil parameters (B>=5 T constraint)
- make tol — tolerance analysis
- make gates — run feasibility gates
- make test — pytest
- make env — print versions
