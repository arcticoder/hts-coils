# Multi-stage Dockerfile for soliton validation framework
# Ensures complete reproducibility across platforms

FROM nvidia/cuda:11.8-devel-ubuntu22.04 AS base

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    git \
    cmake \
    build-essential \
    libhdf5-dev \
    libfftw3-dev \
    libopenmpi-dev \
    libeigen3-dev \
    wget \
    curl \
    vim \
    htop \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Python environment stage
FROM base AS python-env

# Upgrade pip and install wheel
RUN python -m pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements_frozen.txt /tmp/

# Install Python dependencies with exact versions for reproducibility
RUN pip install --no-cache-dir -r /tmp/requirements_frozen.txt

# Install JAX with CUDA support for optimization acceleration  
RUN pip install --no-cache-dir \
    jax[cuda11_pip]==0.4.13 \
    jaxlib[cuda11_pip]==0.4.13 \
    -f https://storage.googleapis.com/jax-releases/jax_cuda_releases.html

# Simulation environment stage
FROM python-env AS simulation

# Set working directory
WORKDIR /app

# Copy source code with proper structure
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY config/ /app/config/
COPY tests/ /app/tests/
COPY setup.py /app/
COPY pyproject.toml /app/
COPY README.md /app/

# Install simulation framework in development mode
RUN pip install -e .

# Create directories for data and results
RUN mkdir -p /app/data /app/results /app/figures /app/logs

# Download and extract validation datasets (placeholder for actual implementation)
RUN mkdir -p /app/data/validation && \
    echo "Validation datasets would be downloaded here in production" > /app/data/validation/README.txt

# Configure environment variables for reproducibility
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV NUMBA_CACHE_DIR="/tmp/numba_cache"
ENV JAX_PLATFORM_NAME="gpu"
ENV CUDA_VISIBLE_DEVICES="0"
ENV PYTHONHASHSEED="42"

# Configure for optimal performance
ENV OMP_NUM_THREADS="8"
ENV MKL_NUM_THREADS="8"
ENV OPENBLAS_NUM_THREADS="8"

# Runtime configuration
EXPOSE 8888 8080 6006
VOLUME ["/app/results", "/app/config_user", "/app/data_user"]

# Copy entrypoint script
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Set up non-root user for security
RUN groupadd -r soliton && useradd -r -g soliton -d /app -s /bin/bash soliton
RUN chown -R soliton:soliton /app
USER soliton

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import src.simulation.soliton_plasma; print('OK')" || exit 1

# Default entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["jupyter"]