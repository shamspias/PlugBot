FROM python:3.11-slim-bookworm

WORKDIR /app

# Fix for GPG signature issues and install system dependencies
RUN set -ex && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /usr/share/keyrings && \
    apt-get update -o Acquire::AllowInsecureRepositories=true -o Acquire::AllowDowngradeToInsecureRepositories=true && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy alembic configuration
COPY alembic.ini .
COPY alembic ./alembic

# Copy application code
COPY app ./app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start application
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]