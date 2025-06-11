# Multi-stage build for frontend optimization
FROM python:3.9-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r streamlituser && useradd -r -g streamlituser streamlituser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=streamlituser:streamlituser . .

# Create necessary directories with proper permissions
RUN mkdir -p .streamlit logs /app/.streamlit && \
    chown -R streamlituser:streamlituser /app && \
    chown -R streamlituser:streamlituser /app/.streamlit

# Set Streamlit environment variables 
ENV STREAMLIT_CONFIG_DIR=/app/.streamlit
ENV HOME=/app
ENV STREAMLIT_SERVER_HEADLESS=true

# Keep running as root for now to avoid permission issues
# USER streamlituser

# Expose port
EXPOSE 8501

# Health check with Streamlit-specific endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Simple Streamlit command for testing
CMD ["streamlit", "run", "simple_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false"] 