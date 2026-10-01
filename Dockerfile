# Multi-Stage Production Dockerfile for GitHub Agent AI (OctoAgent)
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Runtime Stage
FROM python:3.11-slim AS runner

WORKDIR /app

# Create unprivileged application user
RUN groupadd -r octo && useradd -r -g octo -d /app -s /sbin/nologin octo

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/octo/.local
ENV PATH=/home/octo/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy source code
COPY --chown=octo:octo src/ ./src/
COPY --chown=octo:octo main.py pyproject.toml README.md ./

USER octo

ENTRYPOINT ["python", "main.py"]
CMD ["scan", "--keyword", "machine learning"]
