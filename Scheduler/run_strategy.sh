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

write_scheduler_log() {
    local message="$1"
    mkdir -p "$(dirname "$LOG_PATH")"
    printf '%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S%z')" "$message" >> "$LOG_PATH"
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

PYTHON_CMD="$(get_python_command)" || {
    write_scheduler_log "Python was not found in PATH"
    exit 1
}

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

rm -f "$STDERR_FILE"
exit "$EXIT_CODE"