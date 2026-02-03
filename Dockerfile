# Dockerfile for RSS Feed App
# Multi-stage build for optimized production image

# ============================================================================
# STAGE 1: Builder
# ============================================================================
FROM python:3.12-slim as builder

WORKDIR /build

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Install Playwright browsers (if enabled)
RUN python -m playwright install chromium

# ============================================================================
# STAGE 2: Runtime
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Add Python packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . /app

# Create necessary directories
RUN mkdir -p /app/cache/flux /app/cache/pycache /app/logs

# Set Python cache prefix
ENV PYTHONPYCACHEPREFIX=/app/cache/pycache

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/api/health || exit 1

# Run application
CMD ["python", "main.py"]