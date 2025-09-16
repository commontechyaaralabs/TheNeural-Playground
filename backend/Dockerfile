# Use Ubuntu base for better TensorFlow compatibility
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        gcc \
        g++ \
        wget \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --upgrade --force-reinstall -r requirements.txt && \
    pip check && \
    pip cache purge

# Install spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create non-root user (Ubuntu style)
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/false -m appuser && \
    chown -R appuser:appgroup /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose port (Cloud Run will override this with PORT env var)
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    PYTHONIOENCODING=utf-8

# Health check with longer timeout for Cloud Run
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=5 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Start the FastAPI application with uvicorn using PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 120