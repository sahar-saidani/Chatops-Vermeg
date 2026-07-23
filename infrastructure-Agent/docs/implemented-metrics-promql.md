# Implemented Metrics and PromQL Queries

This document lists every implemented metric category and the PromQL query used by the Infrastructure Agent.

## CPU

- Overall CPU usage:
  - `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- Per-core CPU usage:
  - `100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)`
- CPU mode percentages (user, system, idle, nice, iowait, irq, softirq, steal):
  - `avg(rate(node_cpu_seconds_total{mode="<mode>"}[5m])) * 100`
- Load average 1m:
  - `node_load1`
- Load average 5m:
  - `node_load5`
- Load average 15m:
  - `node_load15`
- CPU frequency (primary):
  - `avg(node_cpu_scaling_frequency_hertz)`
- CPU frequency (fallback):
  - `avg(node_cpu_frequency_hertz)`

## Memory

- Total memory:
  - `node_memory_MemTotal_bytes`
- Free memory:
  - `node_memory_MemFree_bytes`
- Available memory:
  - `node_memory_MemAvailable_bytes`
- Cached memory:
  - `node_memory_Cached_bytes`
- Buffers:
  - `node_memory_Buffers_bytes`
- Active memory:
  - `node_memory_Active_bytes`
- Inactive memory:
  - `node_memory_Inactive_bytes`
- Swap total:
  - `node_memory_SwapTotal_bytes`
- Swap free:
  - `node_memory_SwapFree_bytes`
- Memory usage percentage:
  - `100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)`
- Derived:
  - Used memory = total - available
  - Swap used = swap total - swap free

## Disk

- Disk total:
  - `sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})`
- Disk free:
  - `sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})`
- Disk usage percentage:
  - `100 * (1 - (sum(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}) / sum(node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"})))`
- Disk read bytes/sec:
  - `sum(rate(node_disk_read_bytes_total[5m]))`
- Disk write bytes/sec:
  - `sum(rate(node_disk_written_bytes_total[5m]))`
- Read operations/sec:
  - `sum(rate(node_disk_reads_completed_total[5m]))`
- Write operations/sec:
  - `sum(rate(node_disk_writes_completed_total[5m]))`
- Disk IO utilization:
  - `avg(rate(node_disk_io_time_seconds_total[5m])) * 100`
- IO time:
  - `sum(rate(node_disk_io_time_seconds_total[5m]))`
- Read time/sec:
  - `sum(rate(node_disk_read_time_seconds_total[5m]))`
- Write time/sec:
  - `sum(rate(node_disk_write_time_seconds_total[5m]))`
- Derived latency (if available):
  - Read latency = read_time_per_sec / read_ops_per_sec
  - Write latency = write_time_per_sec / write_ops_per_sec

## Filesystem

- Filesystem size per mount:
  - `node_filesystem_size_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}`
- Filesystem free bytes per mount:
  - `node_filesystem_avail_bytes{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}`
- Total files (inodes):
  - `node_filesystem_files{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}`
- Free files (inodes):
  - `node_filesystem_files_free{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}`
- Read-only status:
  - `node_filesystem_readonly{fstype!~"tmpfs|overlay|squashfs|devtmpfs|proc|sysfs"}`
- Derived:
  - Used bytes = total - free
  - Usage % = used / total * 100
  - Used inodes = total files - free files

## Network

- RX bytes/sec:
  - `sum(rate(node_network_receive_bytes_total[5m]))`
- TX bytes/sec:
  - `sum(rate(node_network_transmit_bytes_total[5m]))`
- RX packets/sec:
  - `sum(rate(node_network_receive_packets_total[5m]))`
- TX packets/sec:
  - `sum(rate(node_network_transmit_packets_total[5m]))`
- RX errors/sec:
  - `sum(rate(node_network_receive_errs_total[5m]))`
- TX errors/sec:
  - `sum(rate(node_network_transmit_errs_total[5m]))`
- RX dropped/sec:
  - `sum(rate(node_network_receive_drop_total[5m]))`
- TX dropped/sec:
  - `sum(rate(node_network_transmit_drop_total[5m]))`
- Per-interface RX bytes/sec:
  - `rate(node_network_receive_bytes_total[5m])`
- Per-interface TX bytes/sec:
  - `rate(node_network_transmit_bytes_total[5m])`
- Per-interface RX packets/sec:
  - `rate(node_network_receive_packets_total[5m])`
- Per-interface TX packets/sec:
  - `rate(node_network_transmit_packets_total[5m])`
- Per-interface RX errors/sec:
  - `rate(node_network_receive_errs_total[5m])`
- Per-interface TX errors/sec:
  - `rate(node_network_transmit_errs_total[5m])`
- Per-interface RX dropped/sec:
  - `rate(node_network_receive_drop_total[5m])`
- Per-interface TX dropped/sec:
  - `rate(node_network_transmit_drop_total[5m])`
- Interface state:
  - `node_network_up`

## Processes

- Running processes:
  - `node_procs_running`
- Blocked processes:
  - `node_procs_blocked`
- Process states (if exposed):
  - `node_processes_state`
- Top processes by CPU (if named process metrics available):
  - `topk(5, rate(namedprocess_namegroup_cpu_seconds_total[5m]))`
- Top processes by memory (if named process metrics available):
  - `topk(5, namedprocess_namegroup_memory_bytes)`

## System

- Host metadata:
  - `node_uname_info`
- Boot time:
  - `node_boot_time_seconds`
- Uptime:
  - `time() - node_boot_time_seconds`
- Number of CPUs (logical):
  - `count(node_cpu_seconds_total{mode="idle"})`
- Number of cores:
  - `count(count(node_cpu_seconds_total{mode="idle"}) by (cpu))`
- Logged users:
  - `node_users_logged_in`

## Socket

- TCP connections:
  - `node_sockstat_TCP_inuse`
- UDP sockets:
  - `node_sockstat_UDP_inuse`
- Listening sockets:
  - `node_sockstat_TCP_alloc`
- Established connections:
  - `node_netstat_Tcp_CurrEstab`
- TIME_WAIT:
  - `node_sockstat_TCP_tw`
- CLOSE_WAIT (best effort):
  - `node_netstat_Tcp_CurrEstab{state="CLOSE-WAIT"}`
- CLOSE_WAIT fallback approximation:
  - `node_netstat_TcpExt_TCPAbortOnClose`

## Services

- Running services (if systemd metrics enabled):
  - `count(node_systemd_unit_state{state="active",type="service",name!=""} == 1)`
- Failed services:
  - `count(node_systemd_unit_state{state="failed",name!=""} == 1)`
- Active services:
  - `count(node_systemd_unit_state{state="active",name!=""} == 1)`

## Prometheus

- Target availability:
  - `up`
- Scrape duration:
  - `scrape_duration_seconds`
- Scrape success ratio (%):
  - `avg(up) * 100`
