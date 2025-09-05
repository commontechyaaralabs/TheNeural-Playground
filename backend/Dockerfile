# Alternative approach using Alpine Linux (typically has fewer vulnerabilities)
FROM python:3.12-alpine3.20

# Set working directory
WORKDIR /app

# Install system dependencies (Alpine packages are typically more secure)
RUN apk update && \
    apk upgrade && \
    apk add --no-cache \
        gcc \
        g++ \
        musl-dev \
        linux-headers \
        build-base \
        wget \
        && rm -rf /var/cache/apk/* \
        && rm -rf /tmp/*

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

# Create non-root user (Alpine style)
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup -s /bin/false && \
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