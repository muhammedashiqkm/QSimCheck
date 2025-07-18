# ---------- Stage 1: Build base environment ----------
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install OS-level dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ---------- Stage 2: Install dependencies ----------
FROM base as builder

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python packages
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 3: Final runtime ----------
FROM base

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY . .

# Expose port
EXPOSE 5000

# Default command (Gunicorn for production)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
