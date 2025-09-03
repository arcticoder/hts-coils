#!/usr/bin/env python3
# Script to reproduce key manuscript figures
# Requires: matplotlib, numpy, data from simulation_results.json

import json
import numpy as np
import matplotlib.pyplot as plt

with open('simulation_results.json', 'r') as f:
    data = json.load(f)

# Performance comparison plot
configs = ['Baseline', 'High-Field']
fields = [2.1, 7.07]
margins = [70, 74.5]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

ax1.bar(configs, fields, color=['blue', 'red'])
ax1.set_ylabel('Magnetic Field (T)')
ax1.set_title('Field Strength Comparison')

ax2.bar(configs, margins, color=['blue', 'red'])  
ax2.set_ylabel('Thermal Margin (K)')
ax2.set_title('Thermal Performance')

plt.tight_layout()
plt.savefig('performance_comparison.png', dpi=300)
print("Figure saved: performance_comparison.png")
