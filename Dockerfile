# syntax=docker/dockerfile:1
# Multi-stage build: builder installs deps, runtime copies only venv + app code.

# -----------------------------------------------------------------------------
# Stage 1: install dependencies into a virtual env
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir --no-compile -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# Non-root user (UID/GID 1000)
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

WORKDIR /app

# Use venv from builder (read-only for appuser)
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv

# Application code
COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser src ./src

USER appuser

CMD ["python", "main.py"]
