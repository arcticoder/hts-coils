#!/usr/bin/env python3
"""
Validate HTS coil design against realistic REBCO limits from literature.
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.materials import jc_vs_tb


def validate_rebco_design(N: int = 180, I: float = 45000, R: float = 0.5, 
                         T: float = 20.0, B_est: float = 14.5) -> dict:
    """
    Validate design against realistic REBCO limits.
    
    Based on literature:
    - REBCO Jc ~300 A/mm² at 20K, self-field
    - Typical tape: 4mm wide, 0.1mm thick
    - Derating with field: Jc(B) = Jc0 / (1 + (B/B0)^n)
    """
    # REBCO tape specifications (typical SuperPower or Fujikura)
    tape_width = 4e-3  # m (4mm)
    tape_thickness = 0.1e-3  # m (0.1mm)
    tape_area = tape_width * tape_thickness  # m²
    
    # Critical current density at operating conditions
    Jc_20K_0T = 300e6  # A/m² at 20K, self-field (conservative)
    Jc_operating = jc_vs_tb(T=T, B=B_est, Tc=90, Jc0=Jc_20K_0T, B0=5.0, n=1.5)
    
    # Current capability per tape
    I_per_tape = Jc_operating * tape_area  # A
    
    # Required tapes for design current
    tapes_required = I / I_per_tape
    
    # Conductor cross-section (multiple tapes stacked)
    total_conductor_area = tapes_required * tape_area
    
    # Validate against practical limits
    max_practical_tapes = 50  # Reasonable stacking limit
    is_feasible = tapes_required <= max_practical_tapes
    
    # Calculate realistic current for given constraints
    I_max_realistic = max_practical_tapes * I_per_tape
    
    # Estimate field scaling (B ∝ N*I/R for Helmholtz)
    B_realistic = B_est * (I_max_realistic / I) if I > 0 else 0
    
    return {
        'design_current_A': I,
        'Jc_operating_A_per_mm2': Jc_operating / 1e6,
        'current_per_tape_A': I_per_tape,
        'tapes_required': tapes_required,
        'max_practical_tapes': max_practical_tapes,
        'is_feasible': is_feasible,
        'I_max_realistic_A': I_max_realistic,
        'B_original_T': B_est,
        'B_realistic_T': B_realistic,
        'total_conductor_area_mm2': total_conductor_area * 1e6,
        'derating_factor': Jc_operating / Jc_20K_0T
    }


def realistic_optimization():
    """
    Find realistic design parameters within REBCO constraints.
    """
    print("=== REBCO Design Validation ===")
    
    # Check current design
    current_design = validate_rebco_design()
    
    print(f"Current Design Analysis:")
    print(f"  Design current: {current_design['design_current_A']:.0f} A")
    print(f"  Jc at 20K, 14.5T: {current_design['Jc_operating_A_per_mm2']:.1f} A/mm²")
    print(f"  Current per tape: {current_design['current_per_tape_A']:.0f} A")
    print(f"  Tapes required: {current_design['tapes_required']:.1f}")
    print(f"  Feasible: {current_design['is_feasible']}")
    print(f"  Realistic field: {current_design['B_realistic_T']:.1f} T")
    print(f"  Derating factor: {current_design['derating_factor']:.3f}")
    
    if not current_design['is_feasible']:
        print("\n⚠️  DESIGN NOT FEASIBLE - Too many tapes required!")
        print(f"   Need {current_design['tapes_required']:.1f} tapes per turn")
        print(f"   Practical limit: {current_design['max_practical_tapes']} tapes")
        
        # Find feasible design
        print("\n=== Finding Feasible Design ===")
        
        # Option 1: Reduce current to fit tape limit
        I_feasible = current_design['I_max_realistic_A']
        B_feasible = current_design['B_realistic_T']
        
        print(f"Option 1 - Reduce current:")
        print(f"  I = {I_feasible:.0f} A (was {current_design['design_current_A']:.0f})")
        print(f"  B = {B_feasible:.1f} T (was {current_design['B_original_T']:.1f})")
        
        # Option 2: Increase radius to reduce current needs
        R_new = 0.8  # Larger coil
        I_alt = 25000  # Moderate current
        alt_design = validate_rebco_design(N=180, I=I_alt, R=R_new, B_est=8.0)
        
        print(f"\nOption 2 - Larger coil:")
        print(f"  R = {R_new} m, I = {I_alt} A")
        print(f"  Tapes needed: {alt_design['tapes_required']:.1f}")
        print(f"  Feasible: {alt_design['is_feasible']}")
        print(f"  Estimated field: ~8 T")
        
        return alt_design if alt_design['is_feasible'] else current_design
    else:
        print("\n✅ Design is feasible with realistic REBCO limits!")
        return current_design


if __name__ == "__main__":
    result = realistic_optimization()
    
    print(f"\n=== Summary ===")
    print(f"Realistic field: {result['B_realistic_T']:.1f} T")
    print(f"Conductor area: {result['total_conductor_area_mm2']:.1f} mm²")
    print(f"Tapes per turn: {result['tapes_required']:.1f}")