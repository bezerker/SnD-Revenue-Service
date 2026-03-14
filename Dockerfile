FROM python:3.13-slim

ARG UV_VERSION=0.10.9

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN pip install --no-cache-dir "uv==${UV_VERSION}" \
    && uv sync --frozen --no-dev --no-editable

CMD [".venv/bin/python", "-m", "snd_revenue_service"]
