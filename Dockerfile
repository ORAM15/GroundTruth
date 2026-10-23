# GroundTruth — production image for Render (free web service).
# Local use:  docker build -t groundtruth . && docker run -p 8000:8000 \
#               -e DATABASE_URL=sqlite:////tmp/gt.db -e GEMINI_API_KEY=... groundtruth
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the project (dependencies are the bounded ranges in pyproject.toml).
# Build inputs are copied first so this layer stays cached until they change.
# The GT-4 static UI lives inside the package and ships in the wheel.
COPY pyproject.toml ./
COPY src ./src
RUN pip install .

# Run as an unprivileged user, not root.
RUN useradd --create-home --uid 10001 groundtruth
USER groundtruth

EXPOSE 8000

# Render injects $PORT at runtime; 8000 is the local default.
CMD ["sh", "-c", "uvicorn groundtruth.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
