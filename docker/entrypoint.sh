#!/bin/bash
# Entrypoint script for soliton validation framework Docker container
# Provides flexible execution modes for different use cases

set -e

# Default configuration
DEFAULT_MODE="jupyter"
DATA_DIR="/app/data"
RESULTS_DIR="/app/results"
CONFIG_DIR="/app/config"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Initialize environment
initialize_environment() {
    log "Initializing soliton validation environment..."
    
    # Ensure directories exist
    mkdir -p "$RESULTS_DIR" "$DATA_DIR" "$CONFIG_DIR"
    
    # Set proper permissions
    chmod 755 "$RESULTS_DIR" "$DATA_DIR" "$CONFIG_DIR"
    
    # Initialize random seeds for reproducibility
    export PYTHONHASHSEED=42
    
    # Configure matplotlib backend for headless operation
    export MPLBACKEND=Agg
    
    log "Environment initialized successfully"
}

# Validate GPU availability
check_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1; then
        if nvidia-smi >/dev/null 2>&1; then
            log "GPU acceleration available:"
            nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits
            export JAX_PLATFORM_NAME="gpu"
        else
            warn "NVIDIA driver detected but GPU not accessible"
            export JAX_PLATFORM_NAME="cpu"
        fi
    else
        warn "No GPU detected, using CPU-only mode"
        export JAX_PLATFORM_NAME="cpu"
    fi
}

# Start Jupyter Lab with optimal configuration
start_jupyter() {
    log "Starting Jupyter Lab for interactive development..."
    
    jupyter lab \
        --ip=0.0.0.0 \
        --port=8888 \
        --no-browser \
        --allow-root \
        --notebook-dir=/app \
        --ServerApp.token='soliton-research' \
        --ServerApp.password='' \
        --ServerApp.allow_origin='*' \
        --ServerApp.allow_remote_access=True
}

# Run simulation with specified parameters
run_simulation() {
    log "Running soliton simulation..."
    
    if [ -f "$CONFIG_DIR/simulation_config.json" ]; then
        log "Using custom configuration: $CONFIG_DIR/simulation_config.json"
        python scripts/run_simulation.py --config "$CONFIG_DIR/simulation_config.json"
    else
        log "Using default configuration"
        python scripts/run_simulation.py --config config/default_simulation.json
    fi
}

# Run validation tests
run_validation() {
    log "Running validation test suite..."
    
    # Run unit tests
    python -m pytest tests/ -v --tb=short
    
    # Run integration tests
    python scripts/validation_tests.py
    
    # Verify reproducibility
    python scripts/reproducibility_check.py
    
    log "Validation complete"
}

# Generate all figures
generate_figures() {
    log "Generating publication figures..."
    
    python scripts/reproduce_figures.py --all
    
    log "Figures generated in /app/figures/"
}

# Run benchmarks
run_benchmarks() {
    log "Running performance benchmarks..."
    
    python scripts/benchmark_suite.py --output "$RESULTS_DIR/benchmarks.json"
    
    log "Benchmark results saved to $RESULTS_DIR/benchmarks.json"
}

# Interactive shell mode
start_shell() {
    log "Starting interactive shell..."
    log "Soliton validation framework is ready for interactive use"
    log "Available commands:"
    log "  - soliton-sim: Main simulation tool"
    log "  - python: Python interpreter with all dependencies"
    log "  - jupyter lab: Start Jupyter interface"
    
    exec /bin/bash
}

# Display help information
show_help() {
    cat << EOF
Soliton Validation Framework Docker Container

Usage: docker run [docker-options] soliton-validation:latest [MODE] [OPTIONS]

Available modes:
  jupyter        Start Jupyter Lab for interactive development (default)
  simulation     Run soliton simulation with specified parameters
  validation     Run complete validation test suite
  figures        Generate all publication figures
  benchmarks     Run performance benchmarks
  shell          Start interactive shell
  help           Show this help message

Environment variables:
  CUDA_VISIBLE_DEVICES    GPU device selection (default: 0)
  JAX_PLATFORM_NAME       Force platform: gpu|cpu (auto-detected)
  PYTHONHASHSEED          Random seed for reproducibility (default: 42)

Volume mounts:
  /app/results      Simulation results and outputs
  /app/config_user  User configuration files
  /app/data_user    User data files

Examples:
  # Start Jupyter Lab
  docker run -p 8888:8888 soliton-validation:latest jupyter
  
  # Run simulation with custom config
  docker run -v ./config:/app/config_user soliton-validation:latest simulation
  
  # Generate figures
  docker run -v ./figures:/app/figures soliton-validation:latest figures
  
  # Interactive shell
  docker run -it soliton-validation:latest shell

For more information, visit: https://github.com/arcticoder/hts-coils
EOF
}

# Main execution logic
main() {
    # Parse command line arguments
    MODE="${1:-$DEFAULT_MODE}"
    
    # Initialize environment
    initialize_environment
    check_gpu
    
    # Execute based on mode
    case "$MODE" in
        jupyter)
            start_jupyter
            ;;
        simulation)
            run_simulation
            ;;
        validation)
            run_validation
            ;;
        figures)
            generate_figures
            ;;
        benchmarks)
            run_benchmarks
            ;;
        shell)
            start_shell
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            error "Unknown mode: $MODE. Use 'help' for available options."
            ;;
    esac
}

# Execute main function with all arguments
main "$@"