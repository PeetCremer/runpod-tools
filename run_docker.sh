#!/usr/bin/env bash
# Load .env and run the runpod-tools Docker image with those env vars forwarded.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck source=/dev/null
  source .env
  set +a
fi

exec docker run -p 8888:8888 \
  -e "JUPYTER_PASSWORD=${JUPYTER_PASSWORD:-}" \
  -e "HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN:-}" \
  -e "CIVITAI_TOKEN=${CIVITAI_TOKEN:-}" \
  -e "COMFY_MODEL_ENVS=${COMFY_MODEL_ENVS:-}" \
  -e "RUNPOD_POD_ID=${RUNPOD_POD_ID:-}" \
  --name=runpod-tools \
  jaezred/runpod-tools:release
