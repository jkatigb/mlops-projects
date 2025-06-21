# Multi-stage build for production-ready ML container
# Stage 1: Base dependencies
FROM python:{{cookiecutter.python_version}}-slim AS base

# Security: Run as non-root user
RUN groupadd -r mluser && useradd -r -g mluser mluser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    {% if cookiecutter.include_gpu_support == 'yes' -%}
    nvidia-cuda-toolkit \
    {% endif -%}
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY pyproject.toml .
COPY requirements.txt* ./

# Stage 2: Dependencies installation
FROM base AS dependencies

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install DVC with remote storage support
RUN pip install --no-cache-dir dvc[{{cookiecutter.dvc_remote_type}}]

{% if cookiecutter.use_mlflow == 'yes' -%}
# Install MLflow
RUN pip install --no-cache-dir mlflow
{% endif -%}

{% if cookiecutter.use_wandb == 'yes' -%}
# Install Weights & Biases
RUN pip install --no-cache-dir wandb
{% endif -%}

# Stage 3: Application
FROM dependencies AS app

# Copy application code
COPY --chown=mluser:mluser . .

# Install the package
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs /app/reports && \
    chown -R mluser:mluser /app

# Stage 4: Production runtime
FROM app AS production

# Switch to non-root user
USER mluser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src:$PYTHONPATH

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

{% if cookiecutter.include_api_service == 'yes' -%}
# Expose API port
EXPOSE 8000

# Default command for API service
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
{% else -%}
# Default command
CMD ["python", "-m", "src.models.train"]
{% endif -%}

# Stage 5: Development (optional)
FROM app AS development

# Install development dependencies
RUN pip install --no-cache-dir -e ".[dev,notebook]"

# Switch to non-root user
USER mluser

# Jupyter port
EXPOSE 8888

# Development command
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]