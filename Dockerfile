# pinned by digest: bump the tag and the digest together
ARG PYTHON_IMAGE=python:3.13-alpine3.24@sha256:7984cf56ceaddebe4fefeb75d64000b9f45d8b77b11a09b24524da6cdc3af0c8
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490

FROM ${UV_IMAGE} AS uv


FROM ${PYTHON_IMAGE} AS builder

RUN apk --no-cache add gcc build-base git openssl-dev libffi-dev

COPY --from=uv /uv /uvx /bin/

ARG UV_EXTRA_ARGS="--no-dev"

WORKDIR /app
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-cache --no-install-project ${UV_EXTRA_ARGS} --compile-bytecode

# the project is installed in editable mode, so the sources stay at the same path in the runtime stage
COPY ./ /app/
RUN uv sync --frozen --no-cache ${UV_EXTRA_ARGS} --compile-bytecode && \
    find /app/.venv -perm /022 ! -type l -exec chmod go-w {} +


FROM ${PYTHON_IMAGE}

RUN python -m pip uninstall -y pip

RUN addgroup -S -g 10000 user && \
    adduser -S -D -H -h /app -s /sbin/nologin -G user -u 10000 user

ENV APP_HOME=/app
WORKDIR ${APP_HOME}

# uv is needed at runtime: CI runs `uv sync` and the linters inside this image
COPY --from=uv /uv /uvx /bin/

COPY --from=builder /app/.venv ${APP_HOME}/.venv

COPY ./ ${APP_HOME}/

# code stays root-owned and read-only for the app user (the CI checkout has umask 0000)
RUN python -m compileall -q -x '/(\.venv|tests)/' ${APP_HOME} && \
    find ${APP_HOME} -path ${APP_HOME}/.venv -prune -o -perm /022 -exec chmod go-w {} +

USER 10000:10000

ENV VIRTUAL_ENV=${APP_HOME}/.venv
ENV PATH=${APP_HOME}/.venv/bin:$PATH
ENV UV_CACHE_DIR=/tmp/uv-cache
# `uv run` uses the virtualenv as is: re-syncing would rebuild the project inside the read-only /app
ENV UV_NO_SYNC=1

ENV TZ=Europe/Kiev
ENV LANG="en_US.UTF-8"
ENV LC_ALL="en_US.UTF-8"
ENV LC_LANG="en_US.UTF-8"
ENV PYTHONIOENCODING="UTF-8"

EXPOSE 80

CMD ["gunicorn", "-k", "gevent", "--paste", "/app/etc/service.ini", "--graceful-timeout=60"]
