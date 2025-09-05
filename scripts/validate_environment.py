#!/usr/bin/env python3
"""
Environment Validation Script for Soliton Validation Framework

This script validates the complete environment setup including:
- Python dependencies and versions
- Hardware requirements (CPU, GPU, memory)
- System dependencies
- Data availability
- Configuration integrity

Usage:
    python validate_environment.py [--strict] [--full-check] [--container]
"""

import sys
import subprocess
import platform
import psutil
import importlib
import json
import os
import hashlib
from pathlib import Path
import argparse

class EnvironmentValidator:
    """Comprehensive environment validation for reproducibility."""
    
    def __init__(self, strict_mode=False, container_mode=False):
        self.strict_mode = strict_mode
        self.container_mode = container_mode
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def check_python_version(self):
        """Validate Python version requirements."""
        print("Checking Python version...")
        
        required_version = (3, 9)
        current_version = sys.version_info[:2]
        
        if current_version >= required_version:
            self.validation_results['python_version'] = {
                'status': 'PASS',
                'current': f"{current_version[0]}.{current_version[1]}",
                'required': f"{required_version[0]}.{required_version[1]}"
            }
            print(f"✓ Python {current_version[0]}.{current_version[1]} meets requirements")
        else:
            error_msg = f"Python {current_version[0]}.{current_version[1]} < {required_version[0]}.{required_version[1]} required"
            self.errors.append(error_msg)
            self.validation_results['python_version'] = {
                'status': 'FAIL',
                'current': f"{current_version[0]}.{current_version[1]}",
                'required': f"{required_version[0]}.{required_version[1]}",
                'error': error_msg
            }
            print(f"✗ {error_msg}")
    
    def check_dependencies(self):
        """Validate all required Python dependencies."""
        print("Checking Python dependencies...")
        
        required_packages = {
            'numpy': '1.24.0',
            'scipy': '1.11.0', 
            'matplotlib': '3.7.0',
            'pandas': '2.0.0',
            'h5py': '3.9.0',
            'jax': '0.4.10',
            'numba': '0.57.0',
            'pytest': '7.4.0'
        }
        
        dependency_status = {}
        
        for package, min_version in required_packages.items():
            try:
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    current_version = module.__version__
                    # Simple version comparison (assumes semantic versioning)
                    if self._compare_versions(current_version, min_version) >= 0:
                        dependency_status[package] = {
                            'status': 'PASS',
                            'version': current_version,
                            'required': min_version
                        }
                        print(f"✓ {package} {current_version}")
                    else:
                        error_msg = f"{package} {current_version} < {min_version} required"
                        dependency_status[package] = {
                            'status': 'FAIL',
                            'version': current_version,
                            'required': min_version,
                            'error': error_msg
                        }
                        self.errors.append(error_msg)
                        print(f"✗ {error_msg}")
                else:
                    warning_msg = f"{package} version cannot be determined"
                    dependency_status[package] = {
                        'status': 'WARNING',
                        'version': 'unknown',
                        'required': min_version,
                        'warning': warning_msg
                    }
                    self.warnings.append(warning_msg)
                    print(f"⚠ {warning_msg}")
                    
            except ImportError:
                error_msg = f"{package} is not installed"
                dependency_status[package] = {
                    'status': 'FAIL',
                    'version': 'not installed',
                    'required': min_version,
                    'error': error_msg
                }
                self.errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        self.validation_results['dependencies'] = dependency_status
    
    def check_hardware_requirements(self):
        """Validate hardware requirements."""
        print("Checking hardware requirements...")
        
        hardware_status = {}
        
        # CPU requirements
        cpu_count = psutil.cpu_count(logical=False)
        min_cpu_cores = 4
        
        if cpu_count >= min_cpu_cores:
            hardware_status['cpu'] = {
                'status': 'PASS',
                'cores': cpu_count,
                'required': min_cpu_cores
            }
            print(f"✓ CPU cores: {cpu_count} (>= {min_cpu_cores})")
        else:
            error_msg = f"CPU cores {cpu_count} < {min_cpu_cores} required"
            hardware_status['cpu'] = {
                'status': 'FAIL',
                'cores': cpu_count,
                'required': min_cpu_cores,
                'error': error_msg
            }
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
        
        # Memory requirements
        memory_gb = psutil.virtual_memory().total / (1024**3)
        min_memory_gb = 16
        
        if memory_gb >= min_memory_gb:
            hardware_status['memory'] = {
                'status': 'PASS',
                'total_gb': round(memory_gb, 1),
                'required_gb': min_memory_gb
            }
            print(f"✓ Memory: {memory_gb:.1f} GB (>= {min_memory_gb} GB)")
        else:
            error_msg = f"Memory {memory_gb:.1f} GB < {min_memory_gb} GB required"
            hardware_status['memory'] = {
                'status': 'FAIL',
                'total_gb': round(memory_gb, 1),
                'required_gb': min_memory_gb,
                'error': error_msg
            }
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
        
        # GPU check (optional but recommended)
        try:
            import jax
            devices = jax.devices()
            gpu_devices = [d for d in devices if d.device_kind == 'gpu']
            
            if gpu_devices:
                hardware_status['gpu'] = {
                    'status': 'PASS',
                    'devices': len(gpu_devices),
                    'device_info': [str(d) for d in gpu_devices]
                }
                print(f"✓ GPU devices: {len(gpu_devices)} available")
            else:
                warning_msg = "No GPU devices found (CPU-only mode)"
                hardware_status['gpu'] = {
                    'status': 'WARNING',
                    'devices': 0,
                    'warning': warning_msg
                }
                self.warnings.append(warning_msg)
                print(f"⚠ {warning_msg}")
                
        except Exception as e:
            warning_msg = f"GPU check failed: {e}"
            hardware_status['gpu'] = {
                'status': 'WARNING',
                'error': warning_msg
            }
            self.warnings.append(warning_msg)
            print(f"⚠ {warning_msg}")
        
        self.validation_results['hardware'] = hardware_status
    
    def check_system_dependencies(self):
        """Check system-level dependencies."""
        print("Checking system dependencies...")
        
        system_status = {}
        
        # Check for required system commands
        required_commands = ['git', 'cmake', 'gcc'] if not self.container_mode else ['git']
        
        for cmd in required_commands:
            try:
                result = subprocess.run(['which', cmd], capture_output=True, text=True)
                if result.returncode == 0:
                    system_status[cmd] = {
                        'status': 'PASS',
                        'path': result.stdout.strip()
                    }
                    print(f"✓ {cmd} found at {result.stdout.strip()}")
                else:
                    error_msg = f"{cmd} command not found"
                    system_status[cmd] = {
                        'status': 'FAIL',
                        'error': error_msg
                    }
                    self.errors.append(error_msg)
                    print(f"✗ {error_msg}")
            except Exception as e:
                error_msg = f"Error checking {cmd}: {e}"
                system_status[cmd] = {
                    'status': 'FAIL',
                    'error': error_msg
                }
                self.errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        self.validation_results['system'] = system_status
    
    def check_data_availability(self):
        """Check for required data files and directories."""
        print("Checking data availability...")
        
        data_status = {}
        
        # Expected directory structure
        expected_dirs = [
            'data/',
            'configs/',
            'src/',
            'tests/',
            'scripts/'
        ]
        
        for dir_path in expected_dirs:
            if os.path.exists(dir_path):
                data_status[dir_path] = {
                    'status': 'PASS',
                    'exists': True
                }
                print(f"✓ Directory {dir_path} exists")
            else:
                warning_msg = f"Directory {dir_path} not found"
                data_status[dir_path] = {
                    'status': 'WARNING',
                    'exists': False,
                    'warning': warning_msg
                }
                self.warnings.append(warning_msg)
                print(f"⚠ {warning_msg}")
        
        # Check for key configuration files
        config_files = [
            'requirements_validation.txt',
            'pyproject.toml'
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                data_status[config_file] = {
                    'status': 'PASS',
                    'exists': True
                }
                print(f"✓ Configuration file {config_file} exists")
            else:
                warning_msg = f"Configuration file {config_file} not found"
                data_status[config_file] = {
                    'status': 'WARNING',
                    'exists': False,
                    'warning': warning_msg
                }
                self.warnings.append(warning_msg)
                print(f"⚠ {warning_msg}")
        
        self.validation_results['data'] = data_status
    
    def run_functionality_tests(self):
        """Run basic functionality tests."""
        print("Running functionality tests...")
        
        functionality_status = {}
        
        # Test numpy/scipy functionality
        try:
            import numpy as np
            import scipy.linalg
            
            # Basic linear algebra test
            A = np.random.rand(10, 10)
            eigenvals = scipy.linalg.eigvals(A)
            
            functionality_status['linear_algebra'] = {
                'status': 'PASS',
                'test': 'eigenvalue_computation'
            }
            print("✓ Linear algebra functionality verified")
            
        except Exception as e:
            error_msg = f"Linear algebra test failed: {e}"
            functionality_status['linear_algebra'] = {
                'status': 'FAIL',
                'error': error_msg
            }
            self.errors.append(error_msg)
            print(f"✗ {error_msg}")
        
        # Test JAX functionality (if available)
        try:
            import jax.numpy as jnp
            
            # Basic JAX computation
            x = jnp.array([1.0, 2.0, 3.0])
            y = jnp.sum(x**2)
            
            functionality_status['jax'] = {
                'status': 'PASS',
                'test': 'basic_computation',
                'result': float(y)
            }
            print("✓ JAX functionality verified")
            
        except Exception as e:
            warning_msg = f"JAX test failed: {e}"
            functionality_status['jax'] = {
                'status': 'WARNING',
                'warning': warning_msg
            }
            self.warnings.append(warning_msg)
            print(f"⚠ {warning_msg}")
        
        self.validation_results['functionality'] = functionality_status
    
    def _compare_versions(self, version1, version2):
        """Compare two version strings."""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_tuple(version1)
        v2_tuple = version_tuple(version2)
        
        if v1_tuple > v2_tuple:
            return 1
        elif v1_tuple < v2_tuple:
            return -1
        else:
            return 0
    
    def generate_report(self):
        """Generate validation report."""
        print("\n" + "="*60)
        print("ENVIRONMENT VALIDATION REPORT")
        print("="*60)
        
        total_checks = 0
        passed_checks = 0
        failed_checks = 0
        warning_checks = 0
        
        for category, results in self.validation_results.items():
            print(f"\n{category.upper()}:")
            if isinstance(results, dict):
                for item, status in results.items():
                    total_checks += 1
                    if status['status'] == 'PASS':
                        passed_checks += 1
                        print(f"  ✓ {item}")
                    elif status['status'] == 'FAIL':
                        failed_checks += 1
                        print(f"  ✗ {item}: {status.get('error', 'Unknown error')}")
                    elif status['status'] == 'WARNING':
                        warning_checks += 1
                        print(f"  ⚠ {item}: {status.get('warning', 'Unknown warning')}")
        
        print(f"\nSUMMARY:")
        print(f"  Total checks: {total_checks}")
        print(f"  Passed: {passed_checks}")
        print(f"  Failed: {failed_checks}")
        print(f"  Warnings: {warning_checks}")
        
        if failed_checks == 0:
            if warning_checks == 0:
                print(f"\n🎉 ENVIRONMENT VALIDATION: PASSED")
                return_code = 0
            else:
                print(f"\n⚠️  ENVIRONMENT VALIDATION: PASSED WITH WARNINGS")
                return_code = 0 if not self.strict_mode else 1
        else:
            print(f"\n❌ ENVIRONMENT VALIDATION: FAILED")
            return_code = 1
        
        return return_code
    
    def save_results(self, output_file="validation_results.json"):
        """Save validation results to JSON file."""
        report_data = {
            'timestamp': str(pd.Timestamp.now()),
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'validation_results': self.validation_results,
            'errors': self.errors,
            'warnings': self.warnings,
            'strict_mode': self.strict_mode,
            'container_mode': self.container_mode
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\nValidation results saved to {output_file}")

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description='Validate soliton framework environment')
    parser.add_argument('--strict', action='store_true', 
                       help='Fail on warnings as well as errors')
    parser.add_argument('--full-check', action='store_true',
                       help='Run comprehensive validation including functionality tests')
    parser.add_argument('--container', action='store_true',
                       help='Container mode - skip system dependency checks')
    parser.add_argument('--output', default='validation_results.json',
                       help='Output file for validation results')
    
    args = parser.parse_args()
    
    # Import pandas here to avoid circular dependency issues
    global pd
    import pandas as pd
    
    validator = EnvironmentValidator(strict_mode=args.strict, 
                                   container_mode=args.container)
    
    # Run validation checks
    validator.check_python_version()
    validator.check_dependencies()
    validator.check_hardware_requirements()
    
    if not args.container:
        validator.check_system_dependencies()
    
    validator.check_data_availability()
    
    if args.full_check:
        validator.run_functionality_tests()
    
    # Generate report
    return_code = validator.generate_report()
    
    # Save results
    validator.save_results(args.output)
    
    sys.exit(return_code)

if __name__ == "__main__":
    main()