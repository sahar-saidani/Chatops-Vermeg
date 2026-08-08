#!/usr/bin/env bash
set -euo pipefail

log_message() {
  logger -t logs-agent-test "$1"
}

log_message "TEST LOG FROM LOGS AGENT"
log_message "Custom application log generated for Logs Agent validation"
logger -p authpriv.notice -t sshd "Accepted password for testuser from 127.0.0.1 port 2222 ssh2"
logger -p authpriv.warning -t sshd "Failed password for invalid user demo from 127.0.0.1 port 2222 ssh2"
logger -p kern.err -t kernel "TEST SYSTEM ERROR FROM LOGS AGENT"
logger -p daemon.info -t cron "TEST CRON EVENT FROM LOGS AGENT"

echo "Log generation complete"