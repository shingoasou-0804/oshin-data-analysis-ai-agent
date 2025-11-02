FROM python:3.13-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  git \
  curl \
  ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
COPY uv.lock* ./
RUN uv sync

COPY src ./src
COPY main.py .
COPY .env.example ./
COPY data ./data
COPY scripts ./scripts

RUN useradd -m appuser
USER appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "python", "main.py"]
