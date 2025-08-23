FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    wget \
    unzip \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install optional dependencies for memory monitoring
RUN pip install --no-cache-dir psutil>=5.9.0

# Install gunicorn for production
RUN pip install gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads static/audio flask_session 

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with gunicorn (optimized for memory)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "--max-requests", "1000", "--max-requests-jitter", "100", "--preload", "--worker-class", "sync", "app:app"] 