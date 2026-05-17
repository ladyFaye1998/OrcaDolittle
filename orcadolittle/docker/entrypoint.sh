#!/usr/bin/env bash
# Optional entrypoint wrapper for the OrcaDolittle Docker image.
#
# Sets the cache directory before delegating to the orcadolittle CLI.
# Mount /data as a writable volume to persist the model cache across runs.
set -euo pipefail

mkdir -p "${ORCADOLITTLE_CACHE:-/data/.cache}"
exec orcadolittle "$@"
