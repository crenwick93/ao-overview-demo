#!/usr/bin/env bash
set -eo pipefail

# Fire a test event to the AO workflow trigger endpoint.
# Verifies the workflow can be triggered manually (no EDA needed).
#
# Usage:
#   ./scripts/test-trigger.sh
#   ./scripts/test-trigger.sh '{"request_description":"New server: web01, RHEL 9, prod","requested_by":"Jane Smith"}'
#
# Prerequisites:
#   .env must have AO_WEBHOOK_BASE_URL, AO_WEBHOOK_PATH,
#   AO_WEBHOOK_CLIENT_ID, and AO_WEBHOOK_CLIENT_SECRET set.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${REPO_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env"
  set +a
fi

if [[ -z "${AO_WEBHOOK_BASE_URL:-}" || -z "${AO_WEBHOOK_PATH:-}" || -z "${AO_WEBHOOK_CLIENT_ID:-}" || -z "${AO_WEBHOOK_CLIENT_SECRET:-}" ]]; then
  echo "ERROR: AO webhook credentials not set in .env"
  echo "Required: AO_WEBHOOK_BASE_URL, AO_WEBHOOK_PATH, AO_WEBHOOK_CLIENT_ID, AO_WEBHOOK_CLIENT_SECRET"
  exit 1
fi

PAYLOAD="${1:-{\"request_description\":\"New server needed: webserver-prod-01, RHEL 9, production environment. Needs DNS, monitoring, CMDB, and backup registration.\",\"requested_by\":\"Jane Smith\"}}"

echo "Authenticating with AO..."
TOKEN=$(curl -sk -X POST "${AO_WEBHOOK_BASE_URL}/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=${AO_WEBHOOK_CLIENT_ID}&client_secret=${AO_WEBHOOK_CLIENT_SECRET}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Posting test event to ${AO_WEBHOOK_BASE_URL}/api/v1/webhooks/eda/${AO_WEBHOOK_PATH}..."
RESPONSE=$(curl -sk -X POST "${AO_WEBHOOK_BASE_URL}/api/v1/webhooks/eda/${AO_WEBHOOK_PATH}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "${PAYLOAD}" \
  -w "\n%{http_code}")

HTTP_CODE=$(echo "${RESPONSE}" | tail -1)
BODY=$(echo "${RESPONSE}" | head -n -1)

if [[ "${HTTP_CODE}" == "202" ]]; then
  echo "✅ Workflow triggered successfully"
  echo "${BODY}" | python3 -m json.tool 2>/dev/null || echo "${BODY}"
else
  echo "❌ Failed (HTTP ${HTTP_CODE})"
  echo "${BODY}"
  exit 1
fi
