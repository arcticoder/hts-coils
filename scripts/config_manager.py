#!/usr/bin/env python3
"""
Configuration file ingestion for HTS coil scripts.
Supports JSON configuration with parameter sets and outputs config hash for caching.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class CoilConfig:
    geometry: str = "helmholtz"
    N: int = 200
    I: float = 40000.0
    R: float = 0.4
    separation: Optional[float] = None  # For Helmholtz
    layers: int = 3  # For stack
    axial_spacing: float = 0.2  # For stack
    extent: float = 0.15
    n_grid: int = 61
    z_extent: float = 0.2
    nz_grid: int = 21
    
    def __post_init__(self):
        if self.separation is None and self.geometry == "helmholtz":
            self.separation = self.R


def load_config(config_path: Path) -> CoilConfig:
    """Load configuration from JSON file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    # Extract relevant fields and create config object
    config_data = {}
    for field in CoilConfig.__dataclass_fields__:
        if field in data:
            config_data[field] = data[field]
    
    return CoilConfig(**config_data)


def save_config(config: CoilConfig, config_path: Path):
    """Save configuration to JSON file."""
    with open(config_path, 'w') as f:
        json.dump(asdict(config), f, indent=2)


def config_hash(config: CoilConfig) -> str:
    """Generate a hash of the configuration for caching purposes."""
    # Convert to dict and sort keys for consistent hashing
    config_dict = asdict(config)
    config_str = json.dumps(config_dict, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:8]


def get_cache_path(config: CoilConfig, cache_dir: Path, suffix: str = "") -> Path:
    """Generate cache file path based on config hash."""
    hash_str = config_hash(config)
    filename = f"cache_{hash_str}{suffix}.json"
    return cache_dir / filename


def load_or_compute(config: CoilConfig, cache_dir: Path, compute_func, suffix: str = ""):
    """Load cached result or compute and cache new result."""
    cache_dir.mkdir(exist_ok=True)
    cache_path = get_cache_path(config, cache_dir, suffix)
    
    if cache_path.exists():
        with open(cache_path, 'r') as f:
            return json.load(f)
    else:
        result = compute_func(config)
        with open(cache_path, 'w') as f:
            json.dump(result, f, indent=2)
        return result


def create_example_configs():
    """Create example configuration files."""
    
    # Baseline single loop
    single_config = CoilConfig(
        geometry="single",
        N=400,
        I=50000.0,
        R=0.25,
        extent=0.15,
        n_grid=61
    )
    
    # Optimal Helmholtz pair
    helmholtz_config = CoilConfig(
        geometry="helmholtz",
        N=200,
        I=40000.0,
        R=0.4,
        separation=0.4,
        extent=0.15,
        n_grid=61
    )
    
    # Stack configuration
    stack_config = CoilConfig(
        geometry="stack",
        N=150,
        I=30000.0,
        R=0.3,
        layers=4,
        axial_spacing=0.15,
        extent=0.15,
        n_grid=61
    )
    
    return {
        "single": single_config,
        "helmholtz": helmholtz_config,
        "stack": stack_config
    }


def main():
    """Create example configuration files."""
    import argparse
    
    p = argparse.ArgumentParser(description="Create example HTS coil configurations")
    p.add_argument("--output_dir", type=Path, default=Path("examples"))
    args = p.parse_args()
    
    args.output_dir.mkdir(exist_ok=True)
    
    configs = create_example_configs()
    
    for name, config in configs.items():
        config_path = args.output_dir / f"{name}_config.json"
        save_config(config, config_path)
        print(f"Created {config_path}")
        print(f"  Config hash: {config_hash(config)}")
        print(f"  Geometry: {config.geometry}")
        print(f"  N={config.N}, I={config.I}A, R={config.R}m")
        print()


if __name__ == "__main__":
    main()