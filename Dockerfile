# FootballIQ pipeline image — ingestion + dbt batch jobs.
# API and portal get their own targets in Modules 3/8.
# Tagging (Azure architecture §8): git SHA always; semver on release.

# ---- builder: compilers allowed here, never shipped -------------------------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install ".[pipeline]"

# ---- runtime: slim, non-root, no build tooling ------------------------------
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN useradd --create-home --uid 1000 fiq
WORKDIR /app
COPY --from=builder /install /usr/local
COPY transform ./transform
USER fiq

# No fixed entrypoint: one image, many jobs (ACA Jobs pattern) —
#   python -m footballiq.infrastructure.ingestion
#   dbt run --profiles-dir /app/transform --project-dir /app/transform
CMD ["python", "-c", "import footballiq; print('footballiq pipeline image', footballiq.__version__)"]
