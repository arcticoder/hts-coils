# HTS Coils — Focused, Application-Agnostic Objectives

Refined Objective: Design and validate high-temperature superconducting (HTS) coils achieving a magnetic field strength of 5–10 T with ripple <1%, energy efficiency >99%, and thermal margin >20 mK at operating temperatures <100 K. Target: a scalable coil prototype optimized for critical current density (J_c) and field uniformity.

Quickstart (CI-like local run):
- python scripts/generate_hts_artifacts.py  # writes artifacts/ and feasibility_gates_report.json

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
- docs/VnV-TODO.ndjson — validation tasks and snippet ideas
- docs/UQ-TODO.ndjson — uncertainty quantification tasks and snippet ideas
