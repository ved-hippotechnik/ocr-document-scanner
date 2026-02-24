#!/usr/bin/env bash
#
# deploy.sh — Blue-green deployment script for OCR Document Scanner
#
# Usage:
#   ./deploy.sh deploy   — Build images and perform a blue-green deployment
#   ./deploy.sh rollback — Roll back to the previous deployment
#   ./deploy.sh status   — Show current deployment status
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
readonly PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
readonly STATE_DIR="${PROJECT_ROOT}/.deploy"
readonly ACTIVE_SLOT_FILE="${STATE_DIR}/active_slot"
readonly LOG_FILE="${STATE_DIR}/deploy.log"
readonly HEALTH_ENDPOINT="http://localhost:5000/health"
readonly HEALTH_TIMEOUT=120        # seconds to wait for healthy app
readonly HEALTH_INTERVAL=5         # seconds between health probes

# Compose command — resolved during prerequisite check
COMPOSE_CMD=""

# Colors (disabled when stdout is not a terminal)
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly BLUE='\033[0;34m'
    readonly NC='\033[0m'
else
    readonly RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
_timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log_info() {
    local msg="[$(_timestamp)] [INFO]  $*"
    echo -e "${GREEN}${msg}${NC}"
    echo "${msg}" >> "${LOG_FILE}"
}

log_warn() {
    local msg="[$(_timestamp)] [WARN]  $*"
    echo -e "${YELLOW}${msg}${NC}"
    echo "${msg}" >> "${LOG_FILE}"
}

log_error() {
    local msg="[$(_timestamp)] [ERROR] $*"
    echo -e "${RED}${msg}${NC}" >&2
    echo "${msg}" >> "${LOG_FILE}"
}

log_header() {
    local msg="[$(_timestamp)] ====== $* ======"
    echo -e "${BLUE}${msg}${NC}"
    echo "${msg}" >> "${LOG_FILE}"
}

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------
ensure_state_dir() {
    mkdir -p "${STATE_DIR}"
    touch "${LOG_FILE}"
}

get_active_slot() {
    if [[ -f "${ACTIVE_SLOT_FILE}" ]]; then
        cat "${ACTIVE_SLOT_FILE}"
    else
        echo "none"
    fi
}

set_active_slot() {
    echo "$1" > "${ACTIVE_SLOT_FILE}"
}

get_inactive_slot() {
    local active
    active="$(get_active_slot)"
    if [[ "${active}" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# ---------------------------------------------------------------------------
# Prerequisite checks
# ---------------------------------------------------------------------------
check_prerequisites() {
    log_header "Checking prerequisites"

    # docker
    if ! command -v docker &>/dev/null; then
        log_error "docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    log_info "docker is available"

    # docker-compose (standalone binary) or docker compose (plugin)
    if command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &>/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        log_error "docker-compose (or 'docker compose' plugin) is not installed."
        exit 1
    fi
    log_info "${COMPOSE_CMD} is available"

    # compose file
    if [[ ! -f "${COMPOSE_FILE}" ]]; then
        log_error "docker-compose.yml not found at ${COMPOSE_FILE}"
        exit 1
    fi
    log_info "Compose file found"
}

# Resolve compose command (for commands that skip check_prerequisites)
resolve_compose_cmd() {
    if [[ -n "${COMPOSE_CMD}" ]]; then
        return
    fi
    if command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &>/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        log_error "docker-compose is not available"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Directory setup
# ---------------------------------------------------------------------------
create_directories() {
    log_info "Ensuring required host directories exist"
    mkdir -p "${PROJECT_ROOT}/uploads" \
             "${PROJECT_ROOT}/logs" \
             "${PROJECT_ROOT}/models" \
             "${PROJECT_ROOT}/analytics_charts" \
             "${PROJECT_ROOT}/backups"
}

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
build_images() {
    log_header "Building Docker images"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" build 2>&1 | while IFS= read -r line; do
        echo "  ${line}"
    done
    log_info "Docker images built successfully"
}

# ---------------------------------------------------------------------------
# Save deployment snapshot for rollback
# ---------------------------------------------------------------------------
save_snapshot() {
    local slot="$1"
    log_info "Saving deployment snapshot for slot '${slot}'"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps > "${STATE_DIR}/snapshot_${slot}.txt" 2>/dev/null || true
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" config --images > "${STATE_DIR}/images_${slot}.txt" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Infrastructure (postgres, redis) — shared across blue/green slots
# ---------------------------------------------------------------------------
start_infrastructure() {
    log_header "Starting infrastructure services (PostgreSQL, Redis)"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d postgres redis

    log_info "Waiting for PostgreSQL to become healthy..."
    local waited=0
    while (( waited < 60 )); do
        if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U postgres &>/dev/null; then
            log_info "PostgreSQL is ready"
            break
        fi
        sleep 3
        waited=$((waited + 3))
    done
    if (( waited >= 60 )); then
        log_error "PostgreSQL did not become ready within 60 seconds"
        exit 1
    fi

    log_info "Waiting for Redis to become healthy..."
    waited=0
    while (( waited < 30 )); do
        if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T redis redis-cli ping &>/dev/null; then
            log_info "Redis is ready"
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done
    if (( waited >= 30 )); then
        log_error "Redis did not become ready within 30 seconds"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Application services
# ---------------------------------------------------------------------------
start_application_services() {
    log_header "Starting application services"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d ocr-scanner celery-worker celery-beat
    log_info "Core application containers started"

    # Flower (monitoring) and db-backup are optional
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d flower 2>/dev/null \
        || log_warn "Flower monitoring failed to start (optional)"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" up -d db-backup 2>/dev/null \
        || log_warn "db-backup service failed to start (optional)"
}

stop_application_services() {
    log_info "Stopping application services"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" stop  ocr-scanner celery-worker celery-beat flower db-backup 2>/dev/null || true
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" rm -f ocr-scanner celery-worker celery-beat flower db-backup 2>/dev/null || true
    log_info "Application services stopped"
}

# ---------------------------------------------------------------------------
# Health checks
# ---------------------------------------------------------------------------
wait_for_healthy() {
    log_header "Running health checks"

    local waited=0
    while (( waited < HEALTH_TIMEOUT )); do
        local http_code
        http_code="$(curl -s -o /dev/null -w '%{http_code}' "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")"
        if [[ "${http_code}" == "200" ]]; then
            log_info "Application health check passed (HTTP ${http_code})"
            return 0
        fi
        log_info "Health probe HTTP ${http_code} -- retrying in ${HEALTH_INTERVAL}s (${waited}/${HEALTH_TIMEOUT}s)"
        sleep "${HEALTH_INTERVAL}"
        waited=$((waited + HEALTH_INTERVAL))
    done

    log_error "Application did not become healthy within ${HEALTH_TIMEOUT} seconds"
    return 1
}

run_extended_health_checks() {
    log_info "Verifying database connectivity..."
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T postgres pg_isready -U postgres &>/dev/null; then
        log_info "PostgreSQL connectivity OK"
    else
        log_warn "PostgreSQL connectivity check failed"
    fi

    log_info "Verifying Redis connectivity..."
    if ${COMPOSE_CMD} -f "${COMPOSE_FILE}" exec -T redis redis-cli ping &>/dev/null; then
        log_info "Redis connectivity OK"
    else
        log_warn "Redis connectivity check failed"
    fi
}

# ---------------------------------------------------------------------------
# Core: deploy
# ---------------------------------------------------------------------------
cmd_deploy() {
    log_header "Starting deployment"

    local previous_slot
    previous_slot="$(get_active_slot)"
    local target_slot
    target_slot="$(get_inactive_slot)"

    log_info "Active slot : ${previous_slot}"
    log_info "Target slot : ${target_slot}"

    # Save the current state so we can roll back if needed
    if [[ "${previous_slot}" != "none" ]]; then
        save_snapshot "${previous_slot}"
    fi

    # Step 1 — prerequisites and directories
    check_prerequisites
    create_directories

    # Step 2 — build images
    build_images

    # Step 3 — start shared infrastructure (postgres, redis stay up)
    start_infrastructure

    # Step 4 — swap: stop old application containers, start new ones
    #   Infrastructure services remain running throughout to minimise downtime.
    stop_application_services
    start_application_services

    # Step 5 — verify health
    if wait_for_healthy; then
        run_extended_health_checks
        set_active_slot "${target_slot}"
        save_snapshot "${target_slot}"
        log_header "Deployment successful"
        log_info "Active slot is now '${target_slot}'"
        print_summary
    else
        log_error "Health check failed -- initiating automatic rollback"
        if [[ "${previous_slot}" != "none" ]]; then
            rollback_to_slot "${previous_slot}"
        else
            log_error "No previous deployment to roll back to. Stopping services."
            stop_application_services
            exit 1
        fi
    fi
}

# ---------------------------------------------------------------------------
# Core: rollback (internal helper)
# ---------------------------------------------------------------------------
rollback_to_slot() {
    local target_slot="$1"
    log_header "Rolling back to slot '${target_slot}'"

    stop_application_services

    # Re-launch infrastructure (should still be running, but be safe)
    start_infrastructure
    start_application_services

    if wait_for_healthy; then
        set_active_slot "${target_slot}"
        log_info "Rollback to slot '${target_slot}' succeeded"
        print_summary
    else
        log_error "Rollback ALSO failed. Manual intervention required."
        log_error "Inspect with: ${COMPOSE_CMD} -f ${COMPOSE_FILE} logs"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Core: rollback (user-facing)
# ---------------------------------------------------------------------------
cmd_rollback() {
    log_header "Rollback requested"

    local active
    active="$(get_active_slot)"
    if [[ "${active}" == "none" ]]; then
        log_error "No active deployment found. Nothing to roll back."
        exit 1
    fi

    check_prerequisites

    local target_slot
    if [[ "${active}" == "blue" ]]; then
        target_slot="green"
    else
        target_slot="blue"
    fi

    rollback_to_slot "${target_slot}"
}

# ---------------------------------------------------------------------------
# Core: status
# ---------------------------------------------------------------------------
cmd_status() {
    log_header "Deployment status"
    resolve_compose_cmd

    echo ""
    echo "  Active slot : $(get_active_slot)"
    echo "  Deploy log  : ${LOG_FILE}"
    echo ""

    echo "--- Container status ---"
    ${COMPOSE_CMD} -f "${COMPOSE_FILE}" ps 2>/dev/null || echo "  (no running containers)"

    echo ""
    echo "--- Health check ---"
    local http_code
    http_code="$(curl -s -o /dev/null -w '%{http_code}' "${HEALTH_ENDPOINT}" 2>/dev/null || echo "000")"
    if [[ "${http_code}" == "200" ]]; then
        log_info "Application is healthy (HTTP 200)"
    else
        log_warn "Application returned HTTP ${http_code}"
    fi

    echo ""
    echo "--- Service URLs ---"
    echo "  Application : http://localhost:5000"
    echo "  Health check: ${HEALTH_ENDPOINT}"
    echo "  Flower      : http://localhost:5555"
    echo "  PostgreSQL  : localhost:5432"
    echo "  Redis       : localhost:6379"

    echo ""
    echo "--- Disk usage ---"
    printf "  %-20s %s\n" "uploads/" "$(du -sh "${PROJECT_ROOT}/uploads" 2>/dev/null | cut -f1 || echo 'N/A')"
    printf "  %-20s %s\n" "logs/"    "$(du -sh "${PROJECT_ROOT}/logs"    2>/dev/null | cut -f1 || echo 'N/A')"
    printf "  %-20s %s\n" "models/"  "$(du -sh "${PROJECT_ROOT}/models"  2>/dev/null | cut -f1 || echo 'N/A')"
    printf "  %-20s %s\n" "backups/" "$(du -sh "${PROJECT_ROOT}/backups" 2>/dev/null | cut -f1 || echo 'N/A')"
    echo ""
}

# ---------------------------------------------------------------------------
# Summary printed after deploy / rollback
# ---------------------------------------------------------------------------
print_summary() {
    echo ""
    log_header "Deployment summary"
    echo ""
    echo "  Active slot    : $(get_active_slot)"
    echo "  Application    : http://localhost:5000"
    echo "  Health endpoint: ${HEALTH_ENDPOINT}"
    echo "  Flower monitor : http://localhost:5555"
    echo "  PostgreSQL     : localhost:5432"
    echo "  Redis          : localhost:6379"
    echo ""
    echo "  Useful commands:"
    echo "    View logs : ${COMPOSE_CMD} -f ${COMPOSE_FILE} logs -f"
    echo "    Stop all  : ${COMPOSE_CMD} -f ${COMPOSE_FILE} down"
    echo "    Rollback  : $0 rollback"
    echo "    Status    : $0 status"
    echo ""
}

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------
usage() {
    echo "Usage: $0 {deploy|rollback|status}"
    echo ""
    echo "Commands:"
    echo "  deploy   - Build images and perform a blue-green deployment"
    echo "  rollback - Roll back to the previous deployment slot"
    echo "  status   - Show current deployment status and health"
    echo ""
}

# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
main() {
    ensure_state_dir

    local command="${1:-}"

    case "${command}" in
        deploy)
            cmd_deploy
            ;;
        rollback)
            cmd_rollback
            ;;
        status)
            cmd_status
            ;;
        -h|--help|help)
            usage
            exit 0
            ;;
        "")
            log_error "No command specified."
            usage
            exit 1
            ;;
        *)
            log_error "Unknown command: ${command}"
            usage
            exit 1
            ;;
    esac
}

main "$@"
