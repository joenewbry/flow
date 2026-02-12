#!/bin/bash
# Memex Prometheus Health Check
# Run manually or via crontab to monitor all services.
#
# Usage: bash /ssd/memex/scripts/health_check.sh
# Crontab: */5 * * * * /ssd/memex/scripts/health_check.sh >> /ssd/memex/logs/health.log 2>&1
set -uo pipefail

TIMESTAMP=$(date -Iseconds)
FAILURES=0

check() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" >/dev/null 2>&1; then
        echo "$TIMESTAMP OK   $name"
    else
        echo "$TIMESTAMP FAIL $name"
        FAILURES=$((FAILURES + 1))
    fi
}

echo "--- Health Check $TIMESTAMP ---"

# ChromaDB
check "ChromaDB" "curl -sf http://localhost:8000/api/v1/heartbeat"

# Ollama
check "Ollama" "curl -sf http://localhost:11434/api/version"

# Memex Server
check "Memex Server" "curl -sf http://localhost:8082/health"

# Cloudflare Tunnel
check "Cloudflare Tunnel" "systemctl is-active --quiet cloudflared"

# Data directories
for instance in personal walmart alaska; do
    dir="/ssd/memex/data/$instance/ocr"
    if [ -d "$dir" ]; then
        count=$(ls "$dir"/*.json 2>/dev/null | wc -l)
        echo "$TIMESTAMP INFO $instance: $count OCR files"
    else
        echo "$TIMESTAMP WARN $instance: data directory missing"
    fi
done

# Disk usage
DISK_USAGE=$(df /ssd --output=pcent 2>/dev/null | tail -1 | tr -d ' %')
if [ -n "$DISK_USAGE" ]; then
    if [ "$DISK_USAGE" -gt 90 ]; then
        echo "$TIMESTAMP WARN Disk usage: ${DISK_USAGE}%"
        FAILURES=$((FAILURES + 1))
    else
        echo "$TIMESTAMP INFO Disk usage: ${DISK_USAGE}%"
    fi
fi

# Memory usage
MEM_USED=$(free -m 2>/dev/null | awk '/^Mem:/ {printf "%.0f", $3/$2*100}')
if [ -n "$MEM_USED" ]; then
    echo "$TIMESTAMP INFO Memory usage: ${MEM_USED}%"
    if [ "$MEM_USED" -gt 90 ]; then
        echo "$TIMESTAMP WARN Memory usage critical!"
        FAILURES=$((FAILURES + 1))
    fi
fi

echo "--- $FAILURES failures ---"
echo ""

exit $FAILURES
