# Infrastructure Monitoring Agent

Minimal Python agent for collecting current infrastructure health from Prometheus and printing a report.

## Configuration

Set these environment variables in `.env` or your shell:

- `PROMETHEUS_URL`
- `PROMETHEUS_TIMEOUT_SECONDS`
- `TARGET_NAME`
- `LOG_LEVEL`
- `LOG_FILE`

## Run

```bash
python main.py --collect
```

## Notes

- Prometheus must be reachable from the Windows host.
- Node Exporter must expose the `node_*` metrics used by the collectors.
- The agent does not store history and does not require a database.