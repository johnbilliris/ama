#!/usr/bin/env bash
# scripts/rollback.sh — Automated rollback for the disaster-response-hub CD pipeline.
#
# Reverts all four services (api, agents, ingestion, web) to their previous
# known-good revision and verifies health after rollback.
#
# Exit codes:
#   0 — Rollback completed successfully (or first-run bootstrap — nothing to roll back)
#   1 — Rollback failed: one or more services could not be restored
#   2 — Invalid arguments or missing required parameters
#   3 — Azure CLI not available or authentication failure
#   4 — Health check after rollback failed (critical — manual intervention required)
#
# See: specs/feature/017-cd-pipeline/contracts/rollback-script.md

set -euo pipefail

# ── Constants ────────────────────────────────────────────────────────────────

readonly HEALTH_TIMEOUT=30
readonly HEALTH_RETRIES=3
readonly HEALTH_INTERVAL=10

# Service definitions: name|host_type|health_path
readonly -a SERVICE_DEFS=(
  "api|containerapp|/api/health"
  "agents|containerapp|/health"
  "ingestion|containerapp|/health"
  "web|appservice|/"
)

# ── Globals (set by argument parsing) ────────────────────────────────────────

ENVIRONMENT=""
RESOURCE_GROUP=""
REVISION_API=""
REVISION_AGENTS=""
REVISION_INGESTION=""
REVISION_WEB=""
DRY_RUN=false

# ── Logging helpers ──────────────────────────────────────────────────────────

log()      { echo "[ROLLBACK] $*"; }
log_err()  { echo "[ROLLBACK] ❌ $*" >&2; }

# ── Usage ────────────────────────────────────────────────────────────────────

usage() {
  cat <<'EOF'
Usage: scripts/rollback.sh --environment <staging|production> --resource-group <name>
       [--revision-api <rev>] [--revision-agents <rev>]
       [--revision-ingestion <rev>] [--revision-web <id>]
       [--dry-run]

Options:
  --environment       Target environment (staging or production)  [required]
  --resource-group    Azure resource group name                   [required]
  --revision-api      Known-good revision for api service
  --revision-agents   Known-good revision for agents service
  --revision-ingestion Known-good revision for ingestion service
  --revision-web      Known-good deployment ID for web service
  --dry-run           Print planned actions without executing
  -h, --help          Show this help message

Exit codes:
  0  Rollback successful (or nothing to roll back on first run)
  1  Rollback failed
  2  Invalid arguments
  3  Azure CLI not available
  4  Post-rollback health check failed (CRITICAL)
EOF
}

# ── Argument parsing ─────────────────────────────────────────────────────────

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --environment)
        ENVIRONMENT="${2:-}"
        shift 2
        ;;
      --resource-group)
        RESOURCE_GROUP="${2:-}"
        shift 2
        ;;
      --revision-api)
        REVISION_API="${2:-}"
        shift 2
        ;;
      --revision-agents)
        REVISION_AGENTS="${2:-}"
        shift 2
        ;;
      --revision-ingestion)
        REVISION_INGESTION="${2:-}"
        shift 2
        ;;
      --revision-web)
        REVISION_WEB="${2:-}"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        log_err "ERROR: Unknown argument: $1"
        usage
        exit 2
        ;;
    esac
  done
}

# ── Validation ───────────────────────────────────────────────────────────────

validate_inputs() {
  # Check Azure CLI availability
  if ! command -v az &>/dev/null; then
    log_err "ERROR: Azure CLI (az) is not installed or not in PATH"
    exit 3
  fi

  # Validate environment
  if [[ -z "${ENVIRONMENT}" ]]; then
    log_err "ERROR: --environment is required"
    usage
    exit 2
  fi
  if [[ "${ENVIRONMENT}" != "staging" && "${ENVIRONMENT}" != "production" ]]; then
    log_err "ERROR: --environment must be 'staging' or 'production', got '${ENVIRONMENT}'"
    exit 2
  fi

  # Validate resource group
  if [[ -z "${RESOURCE_GROUP}" ]]; then
    log_err "ERROR: --resource-group is required"
    usage
    exit 2
  fi
}

# ── Revision discovery ───────────────────────────────────────────────────────

# Discover the previous active revision for a Container App.
# Outputs the revision name, or empty string if none found.
discover_containerapp_previous_revision() {
  local app_name="$1"
  local full_name="${ENVIRONMENT}-${app_name}"

  # List revisions sorted by creation date (newest first), get the second one
  local revisions
  revisions=$(az containerapp revision list \
    --name "${full_name}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query "[?properties.active==\`true\`].name" \
    -o tsv 2>/dev/null || echo "")

  # Return the second revision (previous one) if it exists
  local prev
  prev=$(echo "${revisions}" | sed -n '2p')
  echo "${prev}"
}

# Discover the previous deployment for an App Service.
discover_appservice_previous_deployment() {
  local app_name="$1"
  local full_name="${ENVIRONMENT}-${app_name}"

  local deployments
  deployments=$(az webapp deployment list-publishing-credentials \
    --name "${full_name}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query "name" \
    -o tsv 2>/dev/null || echo "")

  echo "${deployments}"
}

# ── Rollback execution ───────────────────────────────────────────────────────

rollback_containerapp() {
  local svc_name="$1"
  local target_revision="$2"
  local app_name="${ENVIRONMENT}-${svc_name}"

  if [[ -z "${target_revision}" ]]; then
    # Discover previous revision
    target_revision=$(discover_containerapp_previous_revision "${svc_name}")
    if [[ -z "${target_revision}" ]]; then
      log "INFO: No previous revision found for ${svc_name} — first deployment (bootstrap). Skipping."
      return 0
    fi
  fi

  # Get current active revision
  local current_revision
  current_revision=$(az containerapp revision list \
    --name "${app_name}" \
    --resource-group "${RESOURCE_GROUP}" \
    --query "[?properties.active==\`true\`].name | [0]" \
    -o tsv 2>/dev/null || echo "")

  log "Rolling back ${svc_name}: ${current_revision:-unknown} → ${target_revision}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log "[DRY-RUN] Would activate revision: ${target_revision}"
    log "[DRY-RUN] Would deactivate revision: ${current_revision:-unknown}"
    return 0
  fi

  # Activate previous revision
  az containerapp revision activate \
    --name "${app_name}" \
    --resource-group "${RESOURCE_GROUP}" \
    --revision "${target_revision}" \
    -o none || {
      log_err "ERROR: Failed to activate revision ${target_revision} for ${svc_name}"
      return 1
    }

  # Deactivate current revision (if known)
  if [[ -n "${current_revision}" && "${current_revision}" != "${target_revision}" ]]; then
    az containerapp revision deactivate \
      --name "${app_name}" \
      --resource-group "${RESOURCE_GROUP}" \
      --revision "${current_revision}" \
      -o none || {
        log_err "ERROR: Failed to deactivate revision ${current_revision} for ${svc_name}"
        return 1
      }
  fi

  return 0
}

rollback_appservice() {
  local svc_name="$1"
  local target_deployment="$2"
  local app_name="${ENVIRONMENT}-${svc_name}"

  if [[ -z "${target_deployment}" ]]; then
    log "INFO: No previous deployment specified for ${svc_name} — first deployment (bootstrap). Skipping."
    return 0
  fi

  log "Rolling back ${svc_name}: current → ${target_deployment}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log "[DRY-RUN] Would redeploy ${svc_name} with deployment: ${target_deployment}"
    return 0
  fi

  # For App Service, we redeploy the previous known-good package
  az webapp deployment source config-zip \
    --name "${app_name}" \
    --resource-group "${RESOURCE_GROUP}" \
    --src "${target_deployment}" \
    -o none || {
      log_err "ERROR: Failed to redeploy ${svc_name} from ${target_deployment}"
      return 1
    }

  return 0
}

# ── Health checks ────────────────────────────────────────────────────────────

check_health() {
  local svc_name="$1"
  local health_path="$2"
  local host_type="$3"
  local app_name="${ENVIRONMENT}-${svc_name}"

  # Resolve the FQDN
  local fqdn
  if [[ "${host_type}" == "containerapp" ]]; then
    fqdn=$(az containerapp show \
      --name "${app_name}" \
      --resource-group "${RESOURCE_GROUP}" \
      --query "properties.configuration.ingress.fqdn" \
      -o tsv 2>/dev/null || echo "")
  else
    fqdn=$(az webapp show \
      --name "${app_name}" \
      --resource-group "${RESOURCE_GROUP}" \
      --query "defaultHostName" \
      -o tsv 2>/dev/null || echo "")
  fi

  if [[ -z "${fqdn}" ]]; then
    log_err "ERROR: Could not resolve FQDN for ${svc_name}"
    return 1
  fi

  local url="https://${fqdn}${health_path}"
  local attempt=1

  while [[ ${attempt} -le ${HEALTH_RETRIES} ]]; do
    local start_ms
    start_ms=$(date +%s%N)

    local status_code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" \
      --max-time "${HEALTH_TIMEOUT}" \
      "${url}" 2>/dev/null || echo "000")

    local end_ms
    end_ms=$(date +%s%N)
    local elapsed_ms=$(( (end_ms - start_ms) / 1000000 ))

    if [[ "${status_code}" =~ ^2[0-9]{2}$ ]]; then
      log "${svc_name}: HEALTHY (${status_code}, ${elapsed_ms}ms)"
      return 0
    fi

    log "${svc_name}: attempt ${attempt}/${HEALTH_RETRIES} — HTTP ${status_code} (${elapsed_ms}ms)"

    if [[ ${attempt} -lt ${HEALTH_RETRIES} ]]; then
      sleep "${HEALTH_INTERVAL}"
    fi
    attempt=$((attempt + 1))
  done

  log_err "ERROR: Health check failed for ${svc_name} after ${HEALTH_RETRIES} attempts"
  return 1
}

# ── Main ─────────────────────────────────────────────────────────────────────

main() {
  parse_args "$@"
  validate_inputs

  log "Environment: ${ENVIRONMENT}"
  log "Resource Group: ${RESOURCE_GROUP}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    log "[DRY-RUN] Mode enabled — no changes will be made"
  fi

  # Track rollback results
  local rollback_failed=false
  local first_run_all_skipped=true

  # Execute rollback for each service
  # Container Apps: api, agents, ingestion
  for svc in api agents ingestion; do
    local rev_var="REVISION_${svc^^}"
    local rev_value="${!rev_var}"

    if ! rollback_containerapp "${svc}" "${rev_value}"; then
      rollback_failed=true
    fi

    # Check if this wasn't a skip (i.e., there was something to roll back)
    if [[ -n "${rev_value}" ]] || [[ -n "$(discover_containerapp_previous_revision "${svc}" 2>/dev/null)" ]]; then
      first_run_all_skipped=false
    fi
  done

  # App Service: web
  if ! rollback_appservice "web" "${REVISION_WEB}"; then
    rollback_failed=true
  fi
  if [[ -n "${REVISION_WEB}" ]]; then
    first_run_all_skipped=false
  fi

  # Handle first-run bootstrap (no previous revisions exist)
  if [[ "${first_run_all_skipped}" == "true" && "${DRY_RUN}" != "true" ]]; then
    log "INFO: First deployment detected — no previous revisions to roll back to."
    log "INFO: This is expected for initial bootstrap. Exiting with success."
    log "✅ Rollback skipped (first-run bootstrap)"
    exit 0
  fi

  # Handle rollback failures
  if [[ "${rollback_failed}" == "true" ]]; then
    log_err "CRITICAL: One or more services failed to roll back"
    exit 1
  fi

  # Dry-run mode — skip health checks
  if [[ "${DRY_RUN}" == "true" ]]; then
    log "[DRY-RUN] ✅ Rollback dry-run completed — no changes made"
    exit 0
  fi

  # Post-rollback health checks
  log "Verifying health checks..."
  local health_failed=false

  for entry in "${SERVICE_DEFS[@]}"; do
    IFS='|' read -r svc_name host_type health_path <<< "${entry}"
    if ! check_health "${svc_name}" "${health_path}" "${host_type}"; then
      health_failed=true
    fi
  done

  if [[ "${health_failed}" == "true" ]]; then
    log_err "CRITICAL: Rollback failed — manual intervention required"
    exit 4
  fi

  log "✅ Rollback completed successfully"
  exit 0
}

main "$@"
