FROM python:3.13-slim AS builder


COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


RUN apt-get update && apt install -y git;

ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

# --locked: don't update the lockfile, just download the deps.
RUN uv sync --no-dev --locked --no-editable --no-install-project;


COPY src/ ./src
# hatch fails if the read
RUN uv sync --no-dev --locked --no-editable;

FROM python:3.13-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY --from=builder --chown=root:root /app/.venv /app/.venv
# NOTE: Since we build the package in the previous step, we're not gonna be running it from `src/` instead it will be in `.venv/`
COPY --from=builder --chown=root:root /app/src /app/src
COPY --from=builder --chown=root:root /app/pyproject.toml /app/

ENV PYTHONPATH=/app/.venv/lib/python3.13/site-packages

# TODO: Remove this hack
# RUN apt-get install libxcb-randr0-dev libxcb-xtest0-dev libxcb-xinerama0-dev libxcb-shape0-dev libxcb-xkb-dev ffmpeg libsm6 libxext6 vim -y

WORKDIR /app

# use unbuffered output
CMD ["uv", "run", "image-harvester"]
