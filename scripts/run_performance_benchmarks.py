#!/usr/bin/env python3
"""
Benchmark Suite Runner for Soliton Validation Framework

This script runs comprehensive performance benchmarks to establish
baseline performance metrics and detect performance regressions.

Usage:
    python run_performance_benchmarks.py [--suite SUITE] [--compare-baseline FILE] [--output FILE]
"""

import numpy as np
import scipy.linalg
import time
import json
import sys
import argparse
import platform
import psutil
from pathlib import Path
import subprocess

class PerformanceBenchmark:
    """Performance benchmarking suite for validation framework."""
    
    def __init__(self):
        self.results = {}
        self.system_info = self._collect_system_info()
        
    def _collect_system_info(self):
        """Collect system information for benchmark context."""
        return {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'memory_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': sys.version,
            'numpy_version': np.__version__,
            'scipy_version': getattr(scipy, '__version__', 'unknown')
        }
    
    def benchmark_linear_algebra(self, matrix_sizes=[50, 100, 200]):
        """Benchmark linear algebra operations."""
        print("Benchmarking linear algebra operations...")
        
        la_results = {}
        
        for size in matrix_sizes:
            print(f"  Matrix size: {size}x{size}")
            
            # Generate test matrix
            np.random.seed(42)
            A = np.random.rand(size, size)
            
            # Eigenvalue decomposition
            start_time = time.perf_counter()
            eigenvals = np.linalg.eigvals(A)
            eigvals_time = time.perf_counter() - start_time
            
            # Matrix multiplication
            start_time = time.perf_counter()
            C = np.dot(A, A.T)
            matmul_time = time.perf_counter() - start_time
            
            # LU decomposition
            start_time = time.perf_counter()
            P, L, U = scipy.linalg.lu(A)
            lu_time = time.perf_counter() - start_time
            
            # SVD decomposition
            start_time = time.perf_counter()
            U_svd, s, Vh = np.linalg.svd(A)
            svd_time = time.perf_counter() - start_time
            
            la_results[f"matrix_{size}"] = {
                'eigenvals_time': eigvals_time,
                'matmul_time': matmul_time,
                'lu_time': lu_time,
                'svd_time': svd_time,
                'eigenvals_checksum': np.sum(np.real(eigenvals)),
                'matmul_checksum': np.sum(C),
                'operations_per_second': {
                    'eigenvals': 1.0 / eigvals_time,
                    'matmul': 1.0 / matmul_time,
                    'lu': 1.0 / lu_time,
                    'svd': 1.0 / svd_time
                }
            }
            
            print(f"    Eigenvals: {eigvals_time:.4f}s")
            print(f"    Matrix mult: {matmul_time:.4f}s")
            print(f"    LU decomp: {lu_time:.4f}s")
            print(f"    SVD: {svd_time:.4f}s")
        
        return la_results
    
    def benchmark_fft_operations(self, signal_sizes=[1024, 4096, 16384]):
        """Benchmark FFT operations."""
        print("Benchmarking FFT operations...")
        
        fft_results = {}
        
        for size in signal_sizes:
            print(f"  Signal size: {size}")
            
            # Generate test signal
            np.random.seed(42)
            signal = np.random.random(size) + 1j * np.random.random(size)
            
            # Forward FFT
            start_time = time.perf_counter()
            fft_result = np.fft.fft(signal)
            fft_time = time.perf_counter() - start_time
            
            # Inverse FFT
            start_time = time.perf_counter()
            ifft_result = np.fft.ifft(fft_result)
            ifft_time = time.perf_counter() - start_time
            
            # Real FFT
            real_signal = np.random.random(size)
            start_time = time.perf_counter()
            rfft_result = np.fft.rfft(real_signal)
            rfft_time = time.perf_counter() - start_time
            
            # 2D FFT
            signal_2d = np.random.random((int(np.sqrt(size)), int(np.sqrt(size))))
            start_time = time.perf_counter()
            fft2_result = np.fft.fft2(signal_2d)
            fft2_time = time.perf_counter() - start_time
            
            fft_results[f"signal_{size}"] = {
                'fft_time': fft_time,
                'ifft_time': ifft_time,
                'rfft_time': rfft_time,
                'fft2_time': fft2_time,
                'reconstruction_error': np.abs(signal - ifft_result).max(),
                'throughput_msamples_per_sec': {
                    'fft': size / (fft_time * 1e6),
                    'ifft': size / (ifft_time * 1e6),
                    'rfft': size / (rfft_time * 1e6)
                }
            }
            
            print(f"    FFT: {fft_time:.4f}s")
            print(f"    IFFT: {ifft_time:.4f}s")
            print(f"    Real FFT: {rfft_time:.4f}s")
            print(f"    2D FFT: {fft2_time:.4f}s")
        
        return fft_results
    
    def benchmark_integration_methods(self):
        """Benchmark numerical integration methods."""
        print("Benchmarking numerical integration...")
        
        integration_results = {}
        
        # Test functions
        test_functions = {
            'polynomial': lambda x: x**3 - 2*x**2 + x - 1,
            'trigonometric': lambda x: np.sin(x) * np.cos(x),
            'exponential': lambda x: np.exp(-x**2),
            'oscillatory': lambda x: np.sin(10*x) / (1 + x**2)
        }
        
        for func_name, func in test_functions.items():
            print(f"  Function: {func_name}")
            
            x_points = np.linspace(0, 2*np.pi, 10000)
            y_values = func(x_points)
            
            # Trapezoidal rule
            start_time = time.perf_counter()
            trap_result = np.trapz(y_values, x_points)
            trap_time = time.perf_counter() - start_time
            
            # Simpson's rule (using scipy)
            start_time = time.perf_counter()
            simp_result = scipy.integrate.simpson(y_values, x_points)
            simp_time = time.perf_counter() - start_time
            
            # Cumulative integration
            start_time = time.perf_counter()
            cumulative = scipy.integrate.cumulative_trapezoid(y_values, x_points, initial=0)
            cum_time = time.perf_counter() - start_time
            
            integration_results[func_name] = {
                'trapezoidal_time': trap_time,
                'simpson_time': simp_time,
                'cumulative_time': cum_time,
                'trapezoidal_result': trap_result,
                'simpson_result': simp_result,
                'integration_rate_points_per_sec': {
                    'trapezoidal': len(x_points) / trap_time,
                    'simpson': len(x_points) / simp_time,
                    'cumulative': len(x_points) / cum_time
                }
            }
            
            print(f"    Trapezoidal: {trap_time:.4f}s")
            print(f"    Simpson: {simp_time:.4f}s")
            print(f"    Cumulative: {cum_time:.4f}s")
        
        return integration_results
    
    def benchmark_memory_operations(self):
        """Benchmark memory allocation and operations."""
        print("Benchmarking memory operations...")
        
        memory_results = {}
        
        # Array allocation
        sizes = [1000, 10000, 100000, 1000000]
        
        for size in sizes:
            print(f"  Array size: {size}")
            
            # Allocation
            start_time = time.perf_counter()
            arr = np.zeros(size, dtype=np.float64)
            alloc_time = time.perf_counter() - start_time
            
            # Fill with data
            start_time = time.perf_counter()
            arr[:] = np.random.random(size)
            fill_time = time.perf_counter() - start_time
            
            # Copy operation
            start_time = time.perf_counter()
            arr_copy = arr.copy()
            copy_time = time.perf_counter() - start_time
            
            # Element access
            indices = np.random.randint(0, size, 1000)
            start_time = time.perf_counter()
            values = arr[indices]
            access_time = time.perf_counter() - start_time
            
            memory_results[f"size_{size}"] = {
                'allocation_time': alloc_time,
                'fill_time': fill_time,
                'copy_time': copy_time,
                'access_time': access_time,
                'memory_mb': arr.nbytes / (1024**2),
                'throughput_mb_per_sec': {
                    'allocation': (arr.nbytes / (1024**2)) / alloc_time,
                    'fill': (arr.nbytes / (1024**2)) / fill_time,
                    'copy': (arr.nbytes / (1024**2)) / copy_time
                }
            }
            
            print(f"    Allocation: {alloc_time:.4f}s")
            print(f"    Fill: {fill_time:.4f}s")
            print(f"    Copy: {copy_time:.4f}s")
            print(f"    Access: {access_time:.4f}s")
        
        return memory_results
    
    def benchmark_simulation_components(self):
        """Benchmark simulation-specific components."""
        print("Benchmarking simulation components...")
        
        sim_results = {}
        
        # Particle evolution simulation
        n_particles = 10000
        n_steps = 100
        
        print(f"  Particle simulation: {n_particles} particles, {n_steps} steps")
        
        # Initialize particles
        positions = np.random.uniform(-1, 1, (n_particles, 3))
        velocities = np.random.normal(0, 1, (n_particles, 3))
        
        # Benchmark particle evolution
        start_time = time.perf_counter()
        
        for step in range(n_steps):
            # Simple force calculation (gravitational-like)
            forces = np.zeros_like(positions)
            for i in range(n_particles):
                for j in range(i+1, min(i+100, n_particles)):  # Limited N-body
                    r_vec = positions[j] - positions[i]
                    r_mag = np.linalg.norm(r_vec) + 1e-6  # Softening
                    force_mag = 1.0 / (r_mag**2)
                    force_dir = r_vec / r_mag
                    forces[i] += force_mag * force_dir
                    forces[j] -= force_mag * force_dir
            
            # Update velocities and positions
            velocities += forces * 0.01  # dt = 0.01
            positions += velocities * 0.01
        
        particle_time = time.perf_counter() - start_time
        
        # Field calculation benchmark
        grid_size = 32
        print(f"  Field calculation: {grid_size}³ grid")
        
        x = np.linspace(-1, 1, grid_size)
        y = np.linspace(-1, 1, grid_size)
        z = np.linspace(-1, 1, grid_size)
        X, Y, Z = np.meshgrid(x, y, z)
        
        start_time = time.perf_counter()
        
        # Calculate electromagnetic field
        field_x = np.sin(np.pi * X) * np.cos(np.pi * Y) * np.exp(-Z**2)
        field_y = np.cos(np.pi * X) * np.sin(np.pi * Y) * np.exp(-Z**2)
        field_z = np.exp(-(X**2 + Y**2)) * np.sin(np.pi * Z)
        
        # Calculate field energy
        energy_density = 0.5 * (field_x**2 + field_y**2 + field_z**2)
        total_energy = np.sum(energy_density)
        
        field_time = time.perf_counter() - start_time
        
        sim_results = {
            'particle_simulation': {
                'n_particles': n_particles,
                'n_steps': n_steps,
                'simulation_time': particle_time,
                'particles_per_second': (n_particles * n_steps) / particle_time,
                'final_energy': 0.5 * np.sum(velocities**2)
            },
            'field_calculation': {
                'grid_size': grid_size,
                'total_points': grid_size**3,
                'calculation_time': field_time,
                'points_per_second': (grid_size**3) / field_time,
                'total_energy': total_energy
            }
        }
        
        print(f"    Particle simulation: {particle_time:.4f}s")
        print(f"    Field calculation: {field_time:.4f}s")
        
        return sim_results
    
    def run_complete_benchmark_suite(self):
        """Run the complete benchmark suite."""
        print("="*60)
        print("SOLITON VALIDATION FRAMEWORK PERFORMANCE BENCHMARKS")
        print("="*60)
        
        start_time = time.time()
        
        # Run all benchmark categories
        self.results['linear_algebra'] = self.benchmark_linear_algebra()
        self.results['fft_operations'] = self.benchmark_fft_operations()
        self.results['integration'] = self.benchmark_integration_methods()
        self.results['memory_operations'] = self.benchmark_memory_operations()
        self.results['simulation_components'] = self.benchmark_simulation_components()
        
        total_time = time.time() - start_time
        
        # Add metadata
        self.results['metadata'] = {
            'total_benchmark_time': total_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': self.system_info
        }
        
        print(f"\nTotal benchmark time: {total_time:.2f} seconds")
        
        return self.results
    
    def compare_with_baseline(self, baseline_file):
        """Compare current results with baseline performance."""
        print(f"\nComparing with baseline: {baseline_file}")
        
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
        except FileNotFoundError:
            print(f"Baseline file {baseline_file} not found")
            return None
        
        comparison = {
            'baseline_timestamp': baseline.get('metadata', {}).get('timestamp', 'unknown'),
            'current_timestamp': self.results['metadata']['timestamp'],
            'performance_ratios': {},
            'regressions': [],
            'improvements': []
        }
        
        # Compare key performance metrics
        for category in ['linear_algebra', 'fft_operations', 'simulation_components']:
            if category in baseline and category in self.results:
                comparison['performance_ratios'][category] = {}
                
                if category == 'linear_algebra':
                    for matrix_size in baseline[category]:
                        if matrix_size in self.results[category]:
                            baseline_time = baseline[category][matrix_size]['eigenvals_time']
                            current_time = self.results[category][matrix_size]['eigenvals_time']
                            ratio = current_time / baseline_time
                            
                            comparison['performance_ratios'][category][matrix_size] = ratio
                            
                            if ratio > 1.1:  # 10% slower
                                comparison['regressions'].append({
                                    'category': category,
                                    'test': matrix_size,
                                    'metric': 'eigenvals_time',
                                    'ratio': ratio,
                                    'baseline': baseline_time,
                                    'current': current_time
                                })
                            elif ratio < 0.9:  # 10% faster
                                comparison['improvements'].append({
                                    'category': category,
                                    'test': matrix_size,
                                    'metric': 'eigenvals_time',
                                    'ratio': ratio,
                                    'baseline': baseline_time,
                                    'current': current_time
                                })
        
        # Print comparison summary
        print(f"Performance comparison summary:")
        print(f"  Regressions found: {len(comparison['regressions'])}")
        print(f"  Improvements found: {len(comparison['improvements'])}")
        
        if comparison['regressions']:
            print("\nPerformance regressions:")
            for reg in comparison['regressions'][:5]:  # Show first 5
                print(f"  {reg['category']}/{reg['test']}: {reg['ratio']:.2f}x slower")
        
        if comparison['improvements']:
            print("\nPerformance improvements:")
            for imp in comparison['improvements'][:5]:  # Show first 5
                print(f"  {imp['category']}/{imp['test']}: {imp['ratio']:.2f}x faster")
        
        return comparison

def main():
    """Main benchmark execution function."""
    parser = argparse.ArgumentParser(description='Run performance benchmarks')
    parser.add_argument('--suite', choices=['quick', 'complete'], default='complete',
                       help='Benchmark suite to run')
    parser.add_argument('--compare-baseline', 
                       help='Compare with baseline performance file')
    parser.add_argument('--output', default='performance_benchmarks.json',
                       help='Output file for benchmark results')
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark()
    
    if args.suite == 'quick':
        # Run subset of benchmarks for quick validation
        benchmark.results['linear_algebra'] = benchmark.benchmark_linear_algebra([50, 100])
        benchmark.results['fft_operations'] = benchmark.benchmark_fft_operations([1024, 4096])
        benchmark.results['metadata'] = {
            'suite': 'quick',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': benchmark.system_info
        }
    else:
        # Run complete benchmark suite
        benchmark.run_complete_benchmark_suite()
    
    # Compare with baseline if provided
    comparison = None
    if args.compare_baseline:
        comparison = benchmark.compare_with_baseline(args.compare_baseline)
    
    # Save results
    output_data = {
        'benchmark_results': benchmark.results,
        'baseline_comparison': comparison
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\nBenchmark results saved to {args.output}")
    
    # Return exit code based on performance regressions
    if comparison and comparison.get('regressions'):
        print(f"\nWARNING: {len(comparison['regressions'])} performance regressions detected")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)