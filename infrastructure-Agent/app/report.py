"""Health report formatting and file output."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyzer.health import HealthReport


REPORTS_DIRNAME = "reports"
LATEST_REPORT_FILENAME = "latest_health_report.txt"


def get_reports_directory() -> Path:
    """Return the project-level reports directory."""

    return Path(__file__).resolve().parents[1] / REPORTS_DIRNAME


def ensure_reports_directory() -> Path:
    """Create the reports directory if it does not exist."""

    reports_directory = get_reports_directory()
    reports_directory.mkdir(parents=True, exist_ok=True)
    return reports_directory


def format_timestamp(value: datetime) -> str:
    """Format timestamps for report output."""

    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def format_metric(value: float | None) -> str:
    """Format percent-based metrics for human-readable output."""

    if value is None:
        return "N/A"
    if abs(value - round(value)) < 0.01:
        return f"{round(value):.0f} %"
    return f"{value:.2f} %"


def format_network(value: float | None) -> str:
    """Format network throughput metrics for human-readable output."""

    if value is None:
        return "N/A"
    return f"{value:.2f} B/s"


def format_number(value: float | None) -> str:
    """Format generic numeric values."""

    if value is None:
        return "N/A"
    if abs(value - round(value)) < 0.01:
        return f"{round(value):.0f}"
    return f"{value:.2f}"


def format_percent(value: float | None) -> str:
    """Format percentage values."""

    return format_metric(value)


def format_duration_seconds(value: float | None) -> str:
    """Format duration values in seconds."""

    if value is None:
        return "N/A"
    return f"{value:.2f} s"


def format_bytes(value: float | None) -> str:
    """Format bytes with IEC units."""

    if value is None:
        return "N/A"
    suffixes = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    amount = float(value)
    idx = 0
    while amount >= 1024.0 and idx < len(suffixes) - 1:
        amount /= 1024.0
        idx += 1
    return f"{amount:.2f} {suffixes[idx]}"


def _append_section(lines: list[str], title: str) -> None:
    """Append a section title to report lines."""

    lines.append("")
    lines.append(f"[{title}]")


def _append_kv(lines: list[str], key: str, value: str) -> None:
    """Append a key/value row to report lines."""

    lines.append(f"{key}: {value}")


def build_health_report_text(
    *,
    timestamp: datetime,
    target: str,
    metrics: dict[str, Any],
    health_report: HealthReport,
) -> str:
    """Create the canonical text representation of the current health snapshot."""

    diagnosis = "\n".join(f"- {problem}" for problem in health_report.problems) if health_report.problems else "None"
    recommendations = health_report.recommendation or "No action required"

    cpu = metrics.get("cpu", {})
    memory = metrics.get("memory", {})
    disk = metrics.get("disk", {})
    filesystem = metrics.get("filesystem", {})
    network = metrics.get("network", {})
    processes = metrics.get("processes", {})
    system = metrics.get("system", {})
    socket = metrics.get("socket", {})
    services = metrics.get("services", {})
    prometheus = metrics.get("prometheus", {})

    availability = str(prometheus.get("availability", "DOWN"))

    lines = [
        "====================================",
        "Infrastructure Health Report",
        "====================================",
        "",
        "Timestamp:",
        format_timestamp(timestamp),
        "",
        "Target:",
        target,
        "",
        "Availability:",
        availability,
        "",
        "Overall Health:",
        health_report.status,
    ]

    _append_section(lines, "CPU")
    _append_kv(lines, "Overall Usage", format_percent(cpu.get("overall_usage")))
    mode_usage = cpu.get("mode_usage", {})
    for mode in ("user", "system", "idle", "nice", "iowait", "irq", "softirq", "steal"):
        _append_kv(lines, f"Mode {mode}", format_percent(mode_usage.get(mode)))
    load = cpu.get("load", {})
    _append_kv(lines, "Load 1m", format_number(load.get("1m")))
    _append_kv(lines, "Load 5m", format_number(load.get("5m")))
    _append_kv(lines, "Load 15m", format_number(load.get("15m")))
    _append_kv(lines, "Frequency", f"{format_number(cpu.get('frequency_mhz'))} MHz")
    per_core = cpu.get("per_core_usage", {})
    if per_core:
        lines.append("Per-core usage:")
        for core, value in sorted(per_core.items(), key=lambda item: item[0]):
            lines.append(f"- cpu{core}: {format_percent(value)}")

    _append_section(lines, "Memory")
    _append_kv(lines, "Usage", format_percent(memory.get("usage_percent")))
    _append_kv(lines, "Total", format_bytes(memory.get("total")))
    _append_kv(lines, "Used", format_bytes(memory.get("used")))
    _append_kv(lines, "Free", format_bytes(memory.get("free")))
    _append_kv(lines, "Available", format_bytes(memory.get("available")))
    _append_kv(lines, "Cached", format_bytes(memory.get("cached")))
    _append_kv(lines, "Buffers", format_bytes(memory.get("buffers")))
    _append_kv(lines, "Active", format_bytes(memory.get("active")))
    _append_kv(lines, "Inactive", format_bytes(memory.get("inactive")))
    _append_kv(lines, "Swap Total", format_bytes(memory.get("swap_total")))
    _append_kv(lines, "Swap Used", format_bytes(memory.get("swap_used")))
    _append_kv(lines, "Swap Free", format_bytes(memory.get("swap_free")))

    _append_section(lines, "Disk")
    _append_kv(lines, "Usage", format_percent(disk.get("usage_percent")))
    _append_kv(lines, "Total", format_bytes(disk.get("total")))
    _append_kv(lines, "Used", format_bytes(disk.get("used")))
    _append_kv(lines, "Free", format_bytes(disk.get("free")))
    _append_kv(lines, "Read Throughput", format_network(disk.get("read_bytes_per_sec")))
    _append_kv(lines, "Write Throughput", format_network(disk.get("write_bytes_per_sec")))
    _append_kv(lines, "Read Ops/s", format_number(disk.get("read_ops_per_sec")))
    _append_kv(lines, "Write Ops/s", format_number(disk.get("write_ops_per_sec")))
    _append_kv(lines, "IO Utilization", format_percent(disk.get("io_utilization_percent")))
    _append_kv(lines, "IO Time", format_duration_seconds(disk.get("io_time_seconds_per_sec")))
    latency = disk.get("latency", {})
    _append_kv(lines, "Read Latency", f"{format_number(latency.get('read_ms'))} ms")
    _append_kv(lines, "Write Latency", f"{format_number(latency.get('write_ms'))} ms")

    _append_section(lines, "Filesystem")
    filesystems = filesystem.get("filesystems", [])
    if filesystems:
        for fs in filesystems:
            lines.append(
                f"- {fs.get('mountpoint')} ({fs.get('filesystem_type')}) | usage={format_percent(fs.get('usage_percent'))} "
                f"| total={format_bytes(fs.get('total'))} | free={format_bytes(fs.get('free'))} "
                f"| inodes_used={format_number(fs.get('used_inodes'))} | read_only={fs.get('read_only')}"
            )
    else:
        lines.append("- N/A")

    _append_section(lines, "Network")
    _append_kv(lines, "RX Bytes/s", format_network(network.get("rx_bytes_per_sec")))
    _append_kv(lines, "TX Bytes/s", format_network(network.get("tx_bytes_per_sec")))
    _append_kv(lines, "RX Packets/s", format_number(network.get("rx_packets_per_sec")))
    _append_kv(lines, "TX Packets/s", format_number(network.get("tx_packets_per_sec")))
    _append_kv(lines, "RX Errors/s", format_number(network.get("rx_errors_per_sec")))
    _append_kv(lines, "TX Errors/s", format_number(network.get("tx_errors_per_sec")))
    dropped = network.get("dropped_packets_per_sec", {})
    _append_kv(lines, "Dropped RX/s", format_number(dropped.get("rx")))
    _append_kv(lines, "Dropped TX/s", format_number(dropped.get("tx")))
    interfaces = network.get("interfaces", [])
    if interfaces:
        lines.append("Per-interface:")
        for interface in interfaces:
            lines.append(
                f"- {interface.get('interface')}: state={interface.get('state', 'N/A')} "
                f"rx={format_network(interface.get('rx_bytes_per_sec'))} "
                f"tx={format_network(interface.get('tx_bytes_per_sec'))}"
            )

    _append_section(lines, "Processes")
    counts = processes.get("counts", {})
    _append_kv(lines, "Total", format_number(counts.get("total")))
    _append_kv(lines, "Running", format_number(counts.get("running")))
    _append_kv(lines, "Sleeping", format_number(counts.get("sleeping")))
    _append_kv(lines, "Stopped", format_number(counts.get("stopped")))
    _append_kv(lines, "Zombie", format_number(counts.get("zombie")))
    _append_kv(lines, "Blocked", format_number(counts.get("blocked")))
    top_cpu = processes.get("top_by_cpu", [])
    top_memory = processes.get("top_by_memory", [])
    lines.append("Top by CPU:")
    if top_cpu:
        for row in top_cpu:
            lines.append(f"- {row.get('process')}: {format_number(row.get('cpu_seconds_per_sec'))} cpu/s")
    else:
        lines.append("- N/A")
    lines.append("Top by Memory:")
    if top_memory:
        for row in top_memory:
            lines.append(f"- {row.get('process')}: {format_bytes(row.get('memory_bytes'))}")
    else:
        lines.append("- N/A")

    _append_section(lines, "System")
    _append_kv(lines, "Hostname", str(system.get("hostname", "N/A")))
    _append_kv(lines, "Kernel Version", str(system.get("kernel_version", "N/A")))
    _append_kv(lines, "OS Version", str(system.get("os_version", "N/A")))
    _append_kv(lines, "Architecture", str(system.get("architecture", "N/A")))
    _append_kv(lines, "Boot Time", format_number(system.get("boot_time")))
    _append_kv(lines, "Uptime", format_duration_seconds(system.get("uptime_seconds")))
    _append_kv(lines, "CPUs", format_number(system.get("cpu_logical")))
    _append_kv(lines, "Cores", format_number(system.get("cpu_cores")))
    _append_kv(lines, "Logged Users", format_number(system.get("logged_users")))

    _append_section(lines, "Socket")
    _append_kv(lines, "TCP Connections", format_number(socket.get("tcp_connections")))
    _append_kv(lines, "UDP Sockets", format_number(socket.get("udp_sockets")))
    _append_kv(lines, "Listening Sockets", format_number(socket.get("listening_sockets")))
    _append_kv(lines, "Established", format_number(socket.get("established_connections")))
    _append_kv(lines, "TIME_WAIT", format_number(socket.get("time_wait")))
    _append_kv(lines, "CLOSE_WAIT", format_number(socket.get("close_wait")))

    _append_section(lines, "Services")
    _append_kv(lines, "Running Services", format_number(services.get("running_services")))
    _append_kv(lines, "Failed Services", format_number(services.get("failed_services")))
    _append_kv(lines, "Active Services", format_number(services.get("active_services")))

    _append_section(lines, "Prometheus")
    _append_kv(lines, "Target Availability", availability)
    _append_kv(lines, "Scrape Duration", format_duration_seconds(prometheus.get("scrape_duration_seconds")))
    _append_kv(lines, "Scrape Success", format_percent(prometheus.get("scrape_success_percent")))
    targets = prometheus.get("targets", [])
    if targets:
        lines.append("Targets:")
        for target_item in targets:
            lines.append(
                f"- job={target_item.get('job', 'N/A')} instance={target_item.get('instance', 'N/A')} status={target_item.get('status', 'N/A')}"
            )

    lines.extend(["", "Diagnosis:", diagnosis, "", "Recommendations:", recommendations])
    return "\n".join(lines) + "\n"


def save_latest_health_report(text: str) -> Path:
    """Write the latest health report to the project reports directory."""

    reports_directory = ensure_reports_directory()
    report_path = reports_directory / LATEST_REPORT_FILENAME
    report_path.write_text(text, encoding="utf-8")
    return report_path