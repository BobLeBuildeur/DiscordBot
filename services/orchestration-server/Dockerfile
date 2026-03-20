# Orchestration server — FastAPI agentic orchestrator PoC
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash app

COPY pyproject.toml ./
COPY backend ./backend
COPY prompts ./prompts

RUN mkdir -p data/orchestrator \
    && chown -R app:app /app

RUN pip install --upgrade pip setuptools wheel \
    && pip install .

USER app

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
