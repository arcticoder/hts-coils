# HTS Coil Optimization - Data Package

## Overview
This package contains key simulation data from:
"Optimization of REBCO High-Temperature Superconducting Coils for 
High-Field Applications in Fusion and Antimatter Trapping"

## Contents

### simulation_results.json
Core simulation results for both baseline (2.1 T) and high-field (7.07 T) configurations.

Key results:
- **High-field**: 7.07 T, 0.16% ripple, 74.5 K thermal margin
- **Baseline**: 2.1 T, 0.01% ripple, 70 K thermal margin  

### comsol_template.java
Template for COMSOL Multiphysics validation studies.

### reproduce_figures.py
Python script to reproduce key manuscript figures.
Usage: `python reproduce_figures.py`

## Validation
All results validated against Docker-based reproduction system.
Run `docker run hts-coil-simulator python run_high_field_simulation.py --verbose`

## Generated
2025-09-02 20:26:53

Ready for Zenodo upload and DOI assignment.
