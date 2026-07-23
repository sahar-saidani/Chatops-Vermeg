# Logs Agent

Production-style Logs Agent for a multi-agent observability platform.

## Architecture

```text
Linux logs
  |
  v
Filebeat
  |
  v
Logstash
  |
  v
Python Logs Agent
  |
  v
Structured JSON output
```

```text
Node Exporter
  |
  v
Prometheus :9090
  |
  v
Prometheus API Collector (Python)
  |
  v
/var/log/logs-agent/prometheus_raw.json
  |
  v
Filebeat
  |
  v
Logstash
  |
  v
output/prometheus_structured.json
```

The Logs Agent now includes the existing log normalization path plus a Prometheus metrics collection pipeline. It does not store data in databases, replace Prometheus, scrape metrics itself, or use Elasticsearch/Kibana.

## Project Layout

```text
logs-agent/
  main.py
  collector.py
  parser.py
  models.py
  config.py
  logger.py
  utils.py
  config.yaml
  requirements.txt
  README.md
```

## Installation

### 1. Python environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r logs-agent/requirements.txt
```

### 2. Filebeat

```bash
sudo rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch
sudo tee /etc/yum.repos.d/elastic.repo >/dev/null <<'EOF'
[elastic-8.x]
name=Elastic repository for 8.x packages
baseurl=https://artifacts.elastic.co/packages/8.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
sudo dnf install -y filebeat
```

Copy the provided config into place:

```bash
sudo cp filebeat.yml /etc/filebeat/filebeat.yml
sudo filebeat test config -e
sudo filebeat test output -e
sudo systemctl enable --now filebeat
```

### 3. Logstash

```bash
sudo dnf install -y logstash
sudo cp etc/logstash/conf.d/logs-agent.conf /etc/logstash/conf.d/logs-agent.conf
sudo /usr/share/logstash/bin/logstash --path.settings /etc/logstash -t
sudo systemctl enable --now logstash
```

## Filebeat Setup

The supplied `filebeat.yml` collects:

- `/var/log/logs-agent/prometheus_raw.json` using the `ndjson` parser
- `/var/log/messages`
- `/var/log/secure`
- `/var/log/cron`
- `/var/log/dmesg`
- systemd journal events

It forwards metrics to Logstash on `localhost:5044` and preserves the legacy log inputs.

## Logstash Setup

The supplied pipeline uses:

- `beats` input on `5044`
- JSON parsing for Prometheus metric events
- `grok` parsing for syslog-like messages
- timestamp normalization
- field normalization
- service detection
- log level extraction
- `file` output with `json_lines` codec to `output/prometheus_structured.json` for metric events
- `tcp` output with `json_lines` codec to `127.0.0.1:5000` for the legacy log stream

## Prometheus Installation

Prometheus is assumed to be installed and running at `http://127.0.0.1:9090`. The collector queries the Prometheus HTTP API endpoint `/api/v1/query`.

## Node Exporter Dependency

Node Exporter provides the host metrics exposed to Prometheus. The collector does not scrape Node Exporter directly; it queries Prometheus for aggregated metrics.

## Python Agent Setup

```bash
python logs-agent/main.py
```

By default, the entrypoint runs the Prometheus metrics pipeline, writes `prometheus_raw.json`, and emits the cleaned structured metrics file. Use `--mode logs` to run the legacy TCP log collector or `--mode both` to run both pipelines.

## Running Commands

Start services in order:

```bash
python logs-agent/main.py
sudo systemctl start logstash
sudo systemctl start filebeat
```

## Validation

Health check script:

```bash
python check_services.py
```

It verifies:

- Prometheus `/-/healthy`
- Prometheus runtime info API
- Node Exporter `/metrics`

Generate test logs:

```bash
bash tests/generate_logs.sh
```

## Testing Procedure

1. Start Prometheus and Node Exporter.
2. Run `python logs-agent/main.py`.
3. Start Logstash and Filebeat for the downstream normalization path.
4. Confirm `prometheus_raw.json` and `output/prometheus_structured.json` are created.
5. Run `tests/generate_logs.sh` for the legacy log path if needed.
6. Run `python check_services.py` to confirm service availability.

## Troubleshooting

- If Logstash is unavailable, Filebeat will queue and retry according to its backoff policy.
- If malformed JSON arrives, the agent logs a warning and drops the record.
- If duplicate events appear, the agent suppresses them within the deduplication window.
- If messages are too large, the agent truncates them to the configured length.
- If Prometheus health checks fail, verify `http://127.0.0.1:9090/-/healthy` manually.
- If Node Exporter fails, verify `http://127.0.0.1:9100/metrics` and the service unit.

## Example Output

```json
{
  "timestamp": "2026-07-12T12:30:20",
  "hostname": "centos-vm",
  "service": "prometheus",
  "level": "INFO",
  "process": "prometheus",
  "source": "/var/log/messages",
  "message": "Prometheus server started",
  "tags": ["logs-agent", "prometheus", "monitoring"]
}
```
