# syntax=docker/dockerfile:1

# Build arguments
ARG PYTHON_VERSION=3.12

# Use Python slim image as base
FROM python:${PYTHON_VERSION}-slim

# Metadata
LABEL maintainer="Sisyphus AI"
LABEL description="Streamlit Text Summarizer App"

# Create non-root user for security
RUN groupadd --gid 1000 appuser && useradd --uid 1000 --gid 1000 -m appuser

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY config.toml ./
COPY src/ ./src/

RUN uv pip install --system --no-cache .

COPY data/ ./data/

# Create directories for data persistence and set ownership
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port Streamlit runs on
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Command to run the application
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"] 
