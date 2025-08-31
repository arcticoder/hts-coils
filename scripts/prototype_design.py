#!/usr/bin/env python3
"""
Prototype design specification for scaled HTS coil demonstrator.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hts.materials import enhanced_thermal_simulation, feasibility_summary


def prototype_spec(N: int = 180, I: float = 45000, R: float = 0.5, 
                  scale: float = 0.2) -> Dict[str, Any]:
    """
    Generate detailed prototype specification for scaled demonstrator.
    
    Args:
        N: Number of turns (full scale)
        I: Current per turn (A, full scale)
        R: Coil radius (m, full scale)
        scale: Scale factor for prototype (0.2 = 20% scale)
        
    Returns:
        Dict with complete prototype specifications
    """
    # Scaled dimensions
    R_proto = R * scale
    I_proto = I * scale  # Scale current to maintain similar field
    N_proto = N  # Keep same number of turns
    
    # Calculate prototype field (scales as I/R)
    field_scale = (I_proto / I) / (R_proto / R)  # Should be ~1
    
    # HTS tape specifications
    # Typical REBCO: 4mm wide, 0.1mm thick, Jc ~300 A/mm² at 20K, self-field
    tape_width = 4e-3  # m
    tape_thickness = 0.1e-3  # m
    Jc_20K = 300e6  # A/m² at 20K, low field
    
    # Required tape cross-sectional area
    I_per_tape = Jc_20K * tape_width * tape_thickness  # A per tape
    tapes_per_turn = max(1, int(I_proto / I_per_tape))
    
    # Conductor specifications
    conductor_length = 2 * 3.14159 * R_proto * N_proto * 2  # Helmholtz pair
    total_tape_length = conductor_length * tapes_per_turn
    
    # Mechanical specifications
    hoop_stress_mpa = 4.5e-7 * (I_proto * N_proto)**2 / (R_proto * 1e6)  # Rough estimate
    
    # Thermal analysis for prototype
    thermal = enhanced_thermal_simulation(
        I=I_proto,
        T_base=20.0,
        Q_rad=0.5e-3,  # 0.5mW external heat for smaller prototype
        conductor_length=conductor_length,
        tape_width=tape_width,
        cryo_efficiency=0.15,
        P_cryo=50.0  # Smaller 50W cryocooler for prototype
    )
    
    # Cost estimates (rough)
    tape_cost_per_m = 20.0  # USD per meter for REBCO tape
    total_tape_cost = total_tape_length * tape_cost_per_m
    
    # Assembly specifications
    spec = {
        "prototype_parameters": {
            "scale_factor": scale,
            "geometry": "helmholtz_pair",
            "N_turns": N_proto,
            "I_per_turn_A": I_proto,
            "R_coil_m": R_proto,
            "separation_m": R_proto,  # Standard Helmholtz
            "field_scale_factor": field_scale
        },
        "hts_tape_specs": {
            "tape_type": "REBCO/Hastelloy",
            "width_mm": tape_width * 1000,
            "thickness_mm": tape_thickness * 1000,
            "Jc_at_20K_A_per_mm2": Jc_20K / 1e6,
            "I_per_tape_A": I_per_tape,
            "tapes_per_turn": tapes_per_turn,
            "total_length_m": total_tape_length,
            "estimated_cost_USD": total_tape_cost
        },
        "mechanical_design": {
            "coil_diameter_m": 2 * R_proto,
            "hoop_stress_MPa": hoop_stress_mpa,
            "support_structure": "stainless_steel_bobbin",
            "winding_method": "layer_wound",
            "estimated_mass_kg": total_tape_length * 0.01  # ~10g/m for REBCO tape
        },
        "cryogenic_system": {
            "operating_temperature_K": 20.0,
            "cryocooler_power_W": 50.0,
            "cooling_capacity_W": thermal["Q_cryo_capacity"],
            "thermal_margin_K": thermal["thermal_margin_K"],
            "vacuum_vessel": "required",
            "thermal_shields": "100K_radiation_shield"
        },
        "performance_predictions": {
            "estimated_B_field_T": 14.5 * field_scale,  # Scale from full-size
            "ripple_percent": 0.29,  # Should be similar
            "thermal_stable": thermal["cryo_sufficient"],
            "power_requirement_W": 50.0 + 10.0  # Cryo + controls
        },
        "build_timeline": {
            "tape_procurement_weeks": 8,
            "mechanical_fabrication_weeks": 12, 
            "assembly_and_test_weeks": 6,
            "total_duration_weeks": 26
        }
    }
    
    return spec


def main():
    """Generate prototype specification document."""
    print("=== HTS Coil Prototype Design Specification ===")
    
    # Generate spec for 20% scale prototype
    spec = prototype_spec(N=180, I=45000, R=0.5, scale=0.2)
    
    # Save to file
    (ROOT / "artifacts").mkdir(exist_ok=True)
    spec_file = ROOT / "artifacts" / "prototype_specification.json"
    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)
    
    # Print summary
    print(f"Prototype scale: {spec['prototype_parameters']['scale_factor']*100:.0f}%")
    print(f"Coil radius: {spec['prototype_parameters']['R_coil_m']:.2f} m")
    print(f"Operating current: {spec['prototype_parameters']['I_per_turn_A']:.0f} A")
    print(f"HTS tape length: {spec['hts_tape_specs']['total_length_m']:.1f} m")
    print(f"Estimated field: {spec['performance_predictions']['estimated_B_field_T']:.1f} T")
    print(f"Thermal margin: {spec['cryogenic_system']['thermal_margin_K']:.1f} K")
    print(f"Build time: {spec['build_timeline']['total_duration_weeks']:.0f} weeks")
    print(f"Tape cost: ${spec['hts_tape_specs']['estimated_cost_USD']:.0f}")
    
    print(f"\nSpecification saved to: {spec_file}")
    
    return spec


if __name__ == "__main__":
    main()