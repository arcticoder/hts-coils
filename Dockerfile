# Dockerfile for HTS Coil Optimization Framework
# Provides reproducible environment for high-field simulations

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Copy requirements
COPY requirements.txt requirements-fea.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install optional FEA dependencies (FEniCSx)
RUN pip install --no-cache-dir -r requirements-fea.txt || echo "FEA dependencies skipped (optional)"

# Copy source code
COPY src/ src/
COPY run_high_field_simulation.py ./
COPY test_high_field_simple.py ./
COPY examples/ examples/

# Set Python path
ENV PYTHONPATH=/workspace/src:$PYTHONPATH

# Create results directory
RUN mkdir -p results

# Default command
CMD ["python", "test_high_field_simple.py"]

# Example usage:
# docker build -t hts-coils .
# docker run -v $(pwd)/results:/workspace/results hts-coils
# docker run -it hts-coils bash  # Interactive mode