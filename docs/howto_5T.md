# How to reach 5 T (HTS coil quick recipe)

Goal: B_mean ≥ 5 T with ripple < 1% on the mid-plane.

Steps
- Run optimizer to propose a Helmholtz pair near the classic s≈R separation.
- Validate with the sweep and plots; choose a candidate with ripple ≤ 1%.
- Record configuration below; adapt N, I, R to your constraints.

Example procedure
1. Optimize:
   - scripts/optimize_config.py --geom helmholtz --iters 30
2. Inspect artifacts/best_config.json.
3. Validate with a focused sweep around the solution:
   - scripts/run_sweep.py --geom helmholtz --N <N-50 N N+50> --I <I/2 I 1.5I> --R <R-0.05 R R+0.05> --sep <sep>
4. Check candidates in artifacts/sweep_topk.json and plots in artifacts/.

Assumptions
- Uniform current distribution, discretized Biot–Savart rings.
- HTS efficiency treated as nearly lossless; efficiency metric includes optional small resistive losses if provided.
- Ripple computed as RMS/mean of Bz over sampling square in plane z=0.

Outputs
- artifacts/best_config.json — best found configuration.
- artifacts/sweep_results.csv — grid of runs with extra metrics.
- artifacts/plots_manifest.json — image paths and captions.
