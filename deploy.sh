#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-/www/wwwroot/changsha-predict}"
BRANCH="${BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/predict/api/health}"
BACKUP_ROOT="${BACKUP_ROOT:-/www/backup/changsha-predict}"
RESTART_CMD="${RESTART_CMD:-}"
SERVICE_NAME="${SERVICE_NAME:-}"
APPLY=0

if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run() {
  if [[ "$APPLY" -eq 1 ]]; then
    "$@"
  else
    printf '[dry-run] '
    printf '%q ' "$@"
    printf '\n'
  fi
}

log "Project directory: $PROJECT_DIR"
log "Branch: $BRANCH"
log "Health check: $HEALTH_URL"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ERROR: project directory does not exist: $PROJECT_DIR" >&2
  exit 1
fi

cd "$PROJECT_DIR"

if [[ ! -f "app.py" ]]; then
  echo "ERROR: app.py was not found in $PROJECT_DIR" >&2
  exit 1
fi

log "Current file state"
if [[ -d ".git" ]]; then
  git status --short
  git rev-parse --short HEAD || true
else
  echo "WARNING: this directory is not a Git repository yet."
  echo "Deploy by git pull is unavailable until the server directory is initialized from your repository."
fi

log "Create backup before changing files"
backup_file="$BACKUP_ROOT/$(date '+%Y%m%d_%H%M%S').tar.gz"
run mkdir -p "$BACKUP_ROOT"
run tar \
  --exclude='./.venv' \
  --exclude='./*_venv' \
  --exclude='./__pycache__' \
  --exclude='./logs' \
  -czf "$backup_file" \
  -C "$PROJECT_DIR" .

if [[ ! -d ".git" ]]; then
  echo "Stop: no .git directory. Initialize the server project from Git first, then rerun this script." >&2
  exit 2
fi

if [[ -n "$(git status --short)" && "${ALLOW_DIRTY:-0}" != "1" ]]; then
  echo "Stop: server working tree has local changes. Review them or set ALLOW_DIRTY=1 if you intentionally want to continue." >&2
  exit 3
fi

log "Pull latest code"
run git fetch origin "$BRANCH"
run git pull --ff-only origin "$BRANCH"

log "Install Python dependencies if requirements.txt has real packages"
if [[ -s "requirements.txt" ]] && grep -Ev '^\s*(#|$)' requirements.txt >/dev/null; then
  if [[ -x ".venv/bin/python" ]]; then
    run .venv/bin/python -m pip install -r requirements.txt
  else
    run "$PYTHON_BIN" -m pip install -r requirements.txt
  fi
else
  echo "No third-party dependencies to install."
fi

log "Build/check project"
if [[ -f "scripts/check.py" ]]; then
  run "$PYTHON_BIN" scripts/check.py
else
  run "$PYTHON_BIN" -m py_compile app.py config.py database.py prediction_engine.py
fi

log "Restart service"
if [[ -n "$RESTART_CMD" ]]; then
  if [[ "$APPLY" -eq 1 ]]; then
    bash -lc "$RESTART_CMD"
  else
    echo "[dry-run] $RESTART_CMD"
  fi
elif [[ -n "$SERVICE_NAME" ]]; then
  run systemctl restart "$SERVICE_NAME"
else
  echo "No restart command configured."
  echo "Set RESTART_CMD='...' or SERVICE_NAME='...' after confirming how the server manages this project."
fi

log "Health check"
if command -v curl >/dev/null 2>&1; then
  if [[ "$APPLY" -eq 1 ]]; then
    curl -fsS "$HEALTH_URL"
    printf '\n'
  else
    echo "[dry-run] curl -fsS $HEALTH_URL"
  fi
else
  echo "curl is not installed; skip health check."
fi

log "Done"
