# Infrastructure Agent Configuration

## Environment

Agent OS:
Windows

Monitoring Server:
CentOS VM

Prometheus URL:
http://<PROMETHEUS_IP>:9090

Node Exporter:
http://<NODE_EXPORTER_IP>:9100

## Metrics collected

CPU:
`100 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100`

Memory:
`100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)`

Disk:
`100 * (1 - node_filesystem_avail_bytes / node_filesystem_size_bytes)`

Network:
`rate(node_network_receive_bytes_total[5m])`
`rate(node_network_transmit_bytes_total[5m])`

Availability:
`up`

## Agent execution

Command:

`python app/main.py --collect`

## Output format

Example health report:

```text
====================================
Infrastructure Health Report
====================================

Timestamp:
2026-07-09T14:52:32Z

Target:
CentOS VM

Availability:
UP

CPU Usage:
1.16 %

Memory Usage:
71.87 %

Disk Usage:
17.66 %

Network:
RX: 1908.52 B/s
TX: 1910.92 B/s

Overall Health:
HEALTHY
```
