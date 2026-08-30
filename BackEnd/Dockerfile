# ──────────────────────────────────────────────────────────────
# A&H Careers — Production Docker image for Render deployment.
#
# Build context: repository root (set in render.yaml or Render dashboard).
#
#   docker build -f BackEnd/Dockerfile -t ah-career-backend .
#   docker run -p 8000:8000 --env-file BackEnd/.env ah-career-backend
# ──────────────────────────────────────────────────────────────

FROM python:3.11-slim

WORKDIR /app

# System deps (none needed beyond python for this project, but keep curl for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY BackEnd/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY BackEnd/ ./BackEnd/
COPY Mcp/     ./Mcp/
COPY data/    ./data/

# Pre-seed the database at build time so the first cold request is fast.
# The seed script is insert-only — safe to call even when data already exists.
RUN cd /app/BackEnd && python ../data/seed_db.py

# Production: use the Render-provided PORT or default to 8000.
# --workers 1 because SQLite does not support concurrent writers.
EXPOSE 8000
CMD ["sh", "-c", "cd /app/BackEnd && exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
