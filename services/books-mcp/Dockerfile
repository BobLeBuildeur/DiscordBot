# Books MCP server: dependencies and package are installed into a Python virtual
# environment at /opt/venv (not system site-packages). Run with stdio attached,
# e.g. `docker run -i --rm -e OPENAI_API_KEY -v books_data:/data/books ...`.
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

RUN python -m venv "$VIRTUAL_ENV" \
    && pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /app

COPY pyproject.toml README.md ./
COPY books_mcp ./books_mcp
COPY prompts ./prompts

RUN pip install --no-cache-dir .

ENV BOOKS_DATA_DIR=/data/books
VOLUME ["/data/books"]

CMD ["python", "-m", "books_mcp"]
