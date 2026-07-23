#!/usr/bin/env bash
set -euo pipefail

log_message() {
  logger -t logs-agent-test "$1"
}

restart_service() {
  local service_name="$1"
  if command -v systemctl >/dev/null 2>&1; then
    if systemctl restart "$service_name"; then
      echo "Restarted ${service_name}"
      return 0
    fi
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo systemctl restart "$service_name"
    echo "Restarted ${service_name} via sudo"
    return 0
  fi

  echo "Skipping ${service_name} restart: insufficient privileges or systemctl unavailable" >&2
  return 0
}

restart_service prometheus
restart_service node_exporter

log_message "TEST LOG FROM LOGS AGENT"
log_message "Custom application log generated for Logs Agent validation"
logger -p authpriv.notice -t sshd "Accepted password for testuser from 127.0.0.1 port 2222 ssh2"
logger -p authpriv.warning -t sshd "Failed password for invalid user demo from 127.0.0.1 port 2222 ssh2"
logger -p kern.err -t kernel "TEST SYSTEM ERROR FROM LOGS AGENT"
logger -p daemon.info -t cron "TEST CRON EVENT FROM LOGS AGENT"

echo "Log generation complete"
