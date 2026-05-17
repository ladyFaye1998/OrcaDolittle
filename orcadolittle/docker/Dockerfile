# OrcaDolittle — deployable inference container.
#
# Builds a CPU-or-GPU image with the full closed loop ready to run.
# Typical use:
#
#   docker build -t orcadolittle:latest -f orcadolittle/docker/Dockerfile .
#   docker run --rm -v $PWD/data:/data orcadolittle:latest \
#       loop --hydrophone /data/sample.wav --dry-run
#
# The image is base-Python 3.11 plus the OrcaDolittle wheel plus its
# inference dependencies (no training stack). For GPU inference, build
# FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 instead of python:3.11-slim
# and add the CUDA-matched torch wheels.

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        ffmpeg \
        libsndfile1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY orcadolittle ./orcadolittle

RUN pip install --upgrade pip \
 && pip install -e . \
 && python -c "import orcadolittle; print('OrcaDolittle', orcadolittle.__version__)"

ENV ORCADOLITTLE_CACHE=/data/.cache

ENTRYPOINT ["orcadolittle"]
CMD ["--help"]
