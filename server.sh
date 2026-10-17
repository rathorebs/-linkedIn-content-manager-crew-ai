#!/usr/bin/env bash
# Start, stop or check the LinkedIn Content Manager servers in the background:
#   backend   api.py (FastAPI)          http://127.0.0.1:8000
#   frontend  Vite dev server (React)   http://localhost:5173  (hot reload)
#
# Usage:
#   ./server.sh start   [backend|frontend]   # no name = both
#   ./server.sh stop    [backend|frontend]
#   ./server.sh restart [backend|frontend]
#   ./server.sh status
#   ./server.sh logs    [backend|frontend]   # follow the log (Ctrl+C to exit)
#
# Other ports: PORT=8080 FRONTEND_PORT=5174 ./server.sh start

set -u

# Always work from the project folder, wherever the script is called from.
cd "$(dirname "$0")" || exit 1

PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
LOG_DIR="logs"
PYTHON=".venv/bin/python"
VITE="frontend/node_modules/.bin/vite"

# Older versions of this script kept the backend PID in .server.pid.
[ -f .server.pid ] && mv .server.pid .backend.pid

# ---------- Per-server settings ----------
pid_file() { echo ".$1.pid"; }
log_file() { echo "$LOG_DIR/$1.log"; }

port_of() {
    case "$1" in
        backend) echo "$PORT" ;;
        frontend) echo "$FRONTEND_PORT" ;;
    esac
}

url_of() {
    case "$1" in
        backend) echo "http://127.0.0.1:$PORT" ;;
        frontend) echo "http://localhost:$FRONTEND_PORT" ;;
    esac
}

# Text that must appear in the process command, so we only ever stop our own servers.
command_match() {
    case "$1" in
        backend) echo "api.py" ;;
        frontend) echo "vite" ;;
    esac
}

# Address to poll until the server answers.
ready_url() {
    case "$1" in
        backend) echo "$(url_of backend)/api/health" ;;
        frontend) echo "$(url_of frontend)/" ;;
    esac
}

# ---------- Helpers ----------
# PID of a running server, from its PID file or by finding it on its port.
find_pid() {
    local name="$1" file pid
    file="$(pid_file "$name")"
    if [ -f "$file" ]; then
        pid="$(cat "$file")"
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return
        fi
        rm -f "$file"   # stale file from a server that already exited
    fi

    # Server started some other way (e.g. `python api.py` or `npm run dev`).
    for pid in $(lsof -ti tcp:"$(port_of "$name")" -sTCP:LISTEN 2>/dev/null); do
        if ps -p "$pid" -o command= | grep -q "$(command_match "$name")"; then
            echo "$pid"
            return
        fi
    done
}

launch() {
    local log
    log="$(log_file "$1")"
    case "$1" in
        backend)
            PORT="$PORT" nohup "$PYTHON" api.py </dev/null >>"$log" 2>&1 &
            ;;
        frontend)
            # `exec` makes the PID we save belong to Vite itself, so `stop` can kill it.
            (cd frontend && API_PORT="$PORT" exec nohup ./node_modules/.bin/vite \
                --port "$FRONTEND_PORT" --strictPort) </dev/null >>"$log" 2>&1 &
            ;;
    esac
    echo $! >"$(pid_file "$1")"
}

# Things that must be in place before a server can start.
preflight() {
    case "$1" in
        backend)
            if [ ! -x "$PYTHON" ]; then
                echo "Error: $PYTHON not found. Set up the venv first (see README.md, step 2.1)."
                return 1
            fi
            ;;
        frontend)
            if ! command -v npm >/dev/null 2>&1; then
                echo "Error: npm not found. Install Node.js (see README.md, section 1)."
                return 1
            fi
            if [ ! -x "$VITE" ]; then
                echo "Installing frontend dependencies (first time only)..."
                (cd frontend && npm install) >>"$(log_file frontend)" 2>&1 || {
                    echo "Error: npm install failed. See $(log_file frontend)"
                    return 1
                }
            fi
            ;;
    esac
}

# ---------- Commands ----------
start_one() {
    local name="$1" pid port i
    pid="$(find_pid "$name")"
    if [ -n "$pid" ]; then
        echo "[$name] Already running (PID $pid) at $(url_of "$name")"
        return 0
    fi

    mkdir -p "$LOG_DIR"
    preflight "$name" || return 1

    port="$(port_of "$name")"
    if lsof -ti tcp:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
        echo "[$name] Error: port $port is used by another program."
        return 1
    fi

    launch "$name"

    # Wait up to 30 seconds for the server to answer.
    printf "[%s] Starting" "$name"
    pid="$(cat "$(pid_file "$name")")"
    for i in $(seq 1 30); do
        if curl -sf "$(ready_url "$name")" >/dev/null 2>&1; then
            echo
            echo "[$name] Running (PID $pid) at $(url_of "$name")"
            return 0
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            echo
            echo "[$name] Error: the server exited. Last lines of $(log_file "$name"):"
            tail -n 20 "$(log_file "$name")"
            rm -f "$(pid_file "$name")"
            return 1
        fi
        printf "."
        sleep 1
    done
    echo
    echo "[$name] Started but isn't answering yet. Check: ./server.sh logs $name"
}

stop_one() {
    local name="$1" pid i
    pid="$(find_pid "$name")"
    if [ -z "$pid" ]; then
        echo "[$name] Not running."
        return 0
    fi

    kill "$pid"
    # Give it up to 10 seconds to shut down cleanly, then force it.
    for i in $(seq 1 10); do
        if ! kill -0 "$pid" 2>/dev/null; then
            rm -f "$(pid_file "$name")"
            echo "[$name] Stopped (PID $pid)."
            return 0
        fi
        sleep 1
    done
    kill -9 "$pid" 2>/dev/null
    rm -f "$(pid_file "$name")"
    echo "[$name] Force-stopped (PID $pid)."
}

status_one() {
    local pid
    pid="$(find_pid "$1")"
    if [ -n "$pid" ]; then
        echo "[$1] Running (PID $pid) at $(url_of "$1")"
    else
        echo "[$1] Not running."
    fi
}

start_all() {
    local name ok=0
    for name in "$@"; do
        start_one "$name" || ok=1
    done
    if [ "$ok" -eq 0 ] && [ -n "$(find_pid frontend)" ]; then
        echo
        echo "Open $(url_of frontend)"
    fi
    return "$ok"
}

stop_all() {
    local name ok=0
    for name in "$@"; do
        stop_one "$name" || ok=1
    done
    return "$ok"
}

# Which servers a command applies to: the one named, or both.
case "${2:-all}" in
    all) TARGETS="backend frontend" ;;
    backend | frontend) TARGETS="$2" ;;
    *)
        echo "Unknown server '$2'. Use: backend, frontend, or leave it out for both."
        exit 1
        ;;
esac

# Stop the frontend first, since it depends on the backend.
STOP_ORDER="$(echo "$TARGETS" | tr ' ' '\n' | sort -r | tr '\n' ' ')"

case "${1:-}" in
    start) start_all $TARGETS ;;
    stop) stop_all $STOP_ORDER ;;
    restart) stop_all $STOP_ORDER && start_all $TARGETS ;;
    status)
        for name in $TARGETS; do status_one "$name"; done
        ;;
    logs)
        mkdir -p "$LOG_DIR"
        FILES=""
        for name in $TARGETS; do
            touch "$(log_file "$name")"
            FILES="$FILES $(log_file "$name")"
        done
        tail -f $FILES
        ;;
    *)
        echo "Usage: ./server.sh {start|stop|restart|status|logs} [backend|frontend]"
        exit 1
        ;;
esac
