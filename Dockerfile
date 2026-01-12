FROM python:3.11-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# System deps (psycopg, node for tailwind via django-tailwind)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot && \
    useradd --system --gid 999 --uid 999 --create-home nonroot 

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin


# Install Python deps first (cached)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY . /app

# Install project + dev deps
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

RUN chown -R nonroot:nonroot /app

USER nonroot
ENTRYPOINT []

CMD ["uv", "run", "manage.py", "migrate"]
