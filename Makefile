PY=python3
ART=artifacts

.PHONY: kpi sweep volumetric envelope gates test plots opt tol env

kpi:
	$(PY) scripts/volumetric_kpis.py

sweep:
	$(PY) scripts/run_sweep.py --geom helmholtz --N 200 400 600 --I 20000 40000 80000 --R 0.2 0.3 0.5 --extent 0.1 --n 61 --sep-frac-min 0.8 --sep-frac-max 1.2 --sep-steps 5 --plots

volumetric:
	$(PY) scripts/volumetric_kpis.py --I 20000 --N 400 --R 0.3 --width 0.01 --thickness 0.01

envelope:
	$(PY) scripts/generate_operating_envelope.py

opt:
	$(PY) scripts/optimize_config.py --geom helmholtz --iters 30

plots:
	$(PY) scripts/run_sweep.py --geom single --plots

 tol:
	$(PY) scripts/tolerance_analysis.py

gates:
	$(PY) scripts/metrics_gate.py

test:
	pytest -q

env:
	$(PY) scripts/env_check.py
