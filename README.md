# HTS Coils — Research-stage objectives and prototype artifacts

Refined Objective (research-stage): Explore and evaluate HTS coil design concepts with simulation and prototype metrics intended to inform further study. Example target ranges (e.g., simulated magnetic field strength in the 5–10 T range, ripple targets, and thermal margin targets) are research-stage outcomes or limited prototype results and should be validated with dedicated V&V before being used for engineering decisions or deployment.

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
-- **Caveat**: Thermal margins, material J_c models, and efficiency calculations depend strongly on assumed material parameters, winding patterns, and boundary conditions; interpret reported numbers as illustrative, not prescriptive.

If maintainers publish numeric claims in a public summary, attach UQ artifacts (confidence intervals, sensitivity results, and raw artifact files) under `docs/` and link to them from the README.

**Additional Limitations & Reproducibility Notes:**
- Many reported metrics are based on simulation ensembles or limited bench trials; sample sizes, sensor calibration, and environmental setup are important for reproducing results. Quantify measurement uncertainty when publishing numeric claims.
- When running `scripts/generate_hts_artifacts.py`, capture the environment (Python package versions, OS, random seeds) and include the generated `artifacts/` folder in PRs used to support claims.
- Experimental prototypes may differ from simulation outputs due to manufacturing tolerances and instrumentation configuration. Treat simulation-derived feasibility gates as design guidance that requires independent validation on hardware.

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

## IEEE Journal Figure Generation

For publication in IEEE Transactions on Applied Superconductivity or similar journals, high-resolution figures based on actual simulation data are generated using:

```bash
python scripts/generate_ieee_figures.py
```

This script produces 300 DPI figures suitable for journal submission:

- **field_map.png**: Magnetic field distribution from realistic REBCO coil parameters (N=400 turns, I=1171A, R=0.2m) showing center field strength and ripple characteristics
- **stress_map.png**: Maxwell stress analysis revealing hoop stress distribution and mechanical reinforcement requirements  
- **prototype.png**: Technical schematic with specifications and component layout for experimental validation

### Figure Generation Process:

1. **Magnetic Field Calculation**: Uses Biot-Savart law implementation from `src/hts/coil.py` with discretized current loops
2. **Stress Analysis**: Maxwell stress tensor computation σᵢⱼ = (1/μ₀)[BᵢBⱼ - ½δᵢⱼB²] from field gradients
3. **IEEE Formatting**: 300+ DPI resolution, Times Roman fonts, colorblind-friendly palettes, proper axis labels and units

### Simulation Parameters (Realistic REBCO):
- Turns: 400 (based on 4mm tape width, 0.2mm thickness)
- Current: 1171 A (146 A/mm² current density at 77K)
- Radius: 0.2 m (practical size for laboratory demonstration)
- Field Performance: 2.11 T center field, 40.7% ripple
- Stress Limits: 415.9 MPa maximum hoop stress (exceeds 35 MPa delamination threshold)

Figures are automatically copied to `papers/figures/` for LaTeX compilation. The journal paper can be compiled with:

```bash
cd papers && pdflatex hts_coils_journal_format.tex
```

**Reproducibility**: Figure generation uses deterministic simulation parameters. For uncertainty quantification, run parameter sweeps documented in `docs/UQ-TODO.ndjson`.
