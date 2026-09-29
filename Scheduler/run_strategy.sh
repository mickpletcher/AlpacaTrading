#!/usr/bin/env bash
# Filename: run_strategy.sh
# Purpose: Load local secrets and launch the scheduled paper trading strategy on Unix like systems.
# Author: TODO
#
# Cron example for 9:25 AM ET on weekdays. This assumes the host uses Eastern Time.
# 25 9 * * 1-5 /bin/bash /path/to/Trading/Scheduler/run_strategy.sh

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_PATH="$REPO_ROOT/.env"
STRATEGY_PATH="$REPO_ROOT/Alpaca/paper_trade.py"
LOG_PATH="$REPO_ROOT/Journal/scheduler_log.txt"
STATUS_PATH="$REPO_ROOT/Journal/scheduler_status.json"

write_scheduler_log() {
    local message="$1"
    mkdir -p "$(dirname "$LOG_PATH")"
    printf '%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S%z')" "$message" >> "$LOG_PATH"
}

write_scheduler_status() {
    local started_at="$1"
    local finished_at="$2"
    local exit_code="$3"
    local error_message="$4"
    "$PYTHON_CMD" -c 'import json,sys; print(json.dumps({"schema_version":1,"started_at":sys.argv[1],"finished_at":sys.argv[2],"exit_code":None if sys.argv[3]=="" else int(sys.argv[3]),"error":sys.argv[4]}, indent=2))' "$started_at" "$finished_at" "$exit_code" "$error_message" > "$STATUS_PATH"
}

load_dotenv() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        return
    fi

    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line#${line%%[![:space:]]*}}"
        line="${line%${line##*[![:space:]]}}"
        [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
        [[ "$line" != *=* ]] && continue

        local name="${line%%=*}"
        local value="${line#*=}"
        value="${value%%[[:space:]]#*}"
        export "$name=$value"
    done < "$path"
}

get_python_command() {
    if command -v python >/dev/null 2>&1; then
        printf '%s' "python"
        return 0
    fi

    if command -v python3 >/dev/null 2>&1; then
        printf '%s' "python3"
        return 0
    fi

    return 1
}

mkdir -p "$REPO_ROOT/Journal"
load_dotenv "$ENV_PATH"

STARTED_AT="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

PYTHON_CMD="$(get_python_command)" || {
    write_scheduler_log "Python was not found in PATH"
    printf '{"schema_version":1,"started_at":"%s","finished_at":"%s","exit_code":1,"error":"Python was not found in PATH"}\n' "$STARTED_AT" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$STATUS_PATH"
    exit 1
}

write_scheduler_status "$STARTED_AT" "" "" ""

STDERR_FILE="$(mktemp)"
write_scheduler_log "Starting strategy: $STRATEGY_PATH"

cd "$REPO_ROOT" || exit 1
"$PYTHON_CMD" "$STRATEGY_PATH" 2>"$STDERR_FILE"
EXIT_CODE=$?
STDERR_OUTPUT="$(cat "$STDERR_FILE")"

write_scheduler_log "ExitCode=$EXIT_CODE"
if [[ -n "$STDERR_OUTPUT" ]]; then
    write_scheduler_log "STDERR: $STDERR_OUTPUT"
fi

write_scheduler_status "$STARTED_AT" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$EXIT_CODE" "$STDERR_OUTPUT"

rm -f "$STDERR_FILE"
exit "$EXIT_CODE"
