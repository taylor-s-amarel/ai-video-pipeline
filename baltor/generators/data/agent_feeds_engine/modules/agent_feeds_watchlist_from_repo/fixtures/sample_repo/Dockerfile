ARG PYTHON_VERSION=3.12
FROM --platform=linux/amd64 python:${PYTHON_VERSION}-slim AS base
RUN pip install -r requirements.txt
FROM base AS final
FROM ghcr.io/example/ffmpeg-static:7.1 \
    AS ffmpeg
FROM scratch
