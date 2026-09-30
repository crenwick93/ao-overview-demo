#!/usr/bin/env bash
set -eo pipefail

# Build and optionally push the Decision Environment (DE) and
# Execution Environment (EE) container images.
#
# Usage:
#   ./dependencies/build-images.sh                          # build only
#   ./dependencies/build-images.sh --push                   # build + push
#   REGISTRY=quay.io/myorg ./dependencies/build-images.sh   # custom registry
#
# Prerequisites:
#   - ansible-builder (pip install ansible-builder)
#   - podman or docker
#   - Logged in to your container registry (podman login / docker login)
#   - Logged in to registry.redhat.io for base images (podman login registry.redhat.io)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTRY="${REGISTRY:-YOUR_REGISTRY}"
DE_TAG="${DE_TAG:-${REGISTRY}/snow-de:latest}"
EE_TAG="${EE_TAG:-${REGISTRY}/ao-ee:latest}"
PUSH=false

if [[ "${1:-}" == "--push" ]]; then
  PUSH=true
fi

echo "============================================"
echo "Building Decision Environment (DE)"
echo "  Tag: ${DE_TAG}"
echo "============================================"
ansible-builder build \
  -f "${SCRIPT_DIR}/de/decision-environment.yml" \
  -t "${DE_TAG}" \
  --prune-images \
  -v 2

echo ""
echo "============================================"
echo "Building Execution Environment (EE)"
echo "  Tag: ${EE_TAG}"
echo "============================================"
ansible-builder build \
  -f "${SCRIPT_DIR}/ee/execution-environment.yml" \
  -t "${EE_TAG}" \
  --prune-images \
  -v 2

if [[ "${PUSH}" == "true" ]]; then
  echo ""
  echo "============================================"
  echo "Pushing images"
  echo "============================================"
  podman push "${DE_TAG}"
  echo "  ✅ Pushed ${DE_TAG}"
  podman push "${EE_TAG}"
  echo "  ✅ Pushed ${EE_TAG}"
else
  echo ""
  echo "============================================"
  echo "Images built (not pushed)"
  echo "  DE: ${DE_TAG}"
  echo "  EE: ${EE_TAG}"
  echo "============================================"
  echo "Run with --push to push, or push manually:"
  echo "  podman push ${DE_TAG}"
  echo "  podman push ${EE_TAG}"
fi
