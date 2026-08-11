
"""Infrastructure monitoring agent entry point."""

from __future__ import annotations

import argparse
import logging
import platform
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

import psutil

from analyzer.health import HealthAnalyzer
from collectors.cpu import CPUCollector
from collectors.disk import DiskCollector
from collectors.filesystem import FilesystemCollector
from collectors.memory import MemoryCollector
from collectors.network import NetworkCollector
from collectors.processes import ProcessCollector
from collectors.prometheus import PrometheusCollector
from collectors.services import ServicesCollector
from collectors.socket import SocketCollector
from collectors.system import SystemCollector
from config import (
    Settings,
    ensure_log_directory,
    resolve_project_path,
)
from prometheus_client import (
    PrometheusClient,
    PrometheusClientError,
)
from report import (
    build_health_report_text,
    format_metric,
    format_network,
    save_latest_health_report,
)


# ============================================================
# Logging
# ============================================================

def setup_logging(settings: Settings) -> logging.Logger:
    """Configure console and file logging."""

    log_path = resolve_project_path(settings.log_file)
    ensure_log_directory(str(log_path))

    logger = logging.getLogger("infrastructure_agent")
    logger.setLevel(
        getattr(
            logging,
            settings.log_level.upper(),
            logging.INFO,
        )
    )

    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_048_576,
        backupCount=3,
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        description="Infrastructure Health Monitoring Agent"
    )

    parser.add_argument(
        "--collect",
        action="store_true",
        help="Collect the current health snapshot and exit",
    )

    return parser.parse_args()


# ============================================================
# Operating system detection
# ============================================================

def detect_operating_system(settings: Settings) -> str:
    """
    Determine the operating system used by the infrastructure agent.

    Priority:
        1. OPERATING_SYSTEM environment variable
        2. Settings.operating_system if available
        3. platform.system()

    Returns:
        "LINUX" or "WINDOWS"
    """

    configured_os = getattr(
        settings,
        "operating_system",
        None,
    )

    if not configured_os:
        import os

        configured_os = os.getenv("OPERATING_SYSTEM")

    if configured_os:
        normalized = configured_os.strip().upper()

        if normalized in {"LINUX", "WINDOWS"}:
            return normalized

        raise ValueError(
            "Invalid OPERATING_SYSTEM value: "
            f"{configured_os!r}. "
            "Expected LINUX or WINDOWS."
        )

    detected = platform.system().strip().upper()

    if detected == "LINUX":
        return "LINUX"

    if detected == "WINDOWS":
        return "WINDOWS"

    raise RuntimeError(
        f"Unsupported operating system: {detected}"
    )


# ============================================================
# Windows / psutil collection
# ============================================================

def collect_windows_metrics(
    logger: logging.Logger,
) -> dict[str, Any]:
    """
    Collect infrastructure metrics directly from Windows using psutil.

    This path does NOT require Node Exporter or Prometheus.
    """

    logger.info(
        "Collecting Windows infrastructure metrics using psutil"
    )

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    cpu_percent = psutil.cpu_percent(
        interval=1.0
    )

    cpu_per_core = psutil.cpu_percent(
        interval=None,
        percpu=True,
    )

    cpu_frequency = psutil.cpu_freq()

    cpu_metrics: dict[str, Any] = {
        "overall_usage": cpu_percent,
        "per_core_usage": {
            str(index): value
            for index, value in enumerate(cpu_per_core)
        },
        "mode_usage": {},
        "load": {
            "1m": None,
            "5m": None,
            "15m": None,
        },
        "frequency_mhz": (
            cpu_frequency.current
            if cpu_frequency
            else None
        ),
        "context_switches_per_sec": None,
        "interrupts_per_sec": None,
        "softirqs_per_sec": None,
    }

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()

    memory_metrics: dict[str, Any] = {
        "total": virtual_memory.total,
        "used": virtual_memory.used,
        "free": virtual_memory.free,
        "available": virtual_memory.available,
        "cached": getattr(
            virtual_memory,
            "cached",
            None,
        ),
        "buffers": getattr(
            virtual_memory,
            "buffers",
            None,
        ),
        "active": getattr(
            virtual_memory,
            "active",
            None,
        ),
        "inactive": getattr(
            virtual_memory,
            "inactive",
            None,
        ),
        "swap_total": swap_memory.total,
        "swap_used": swap_memory.used,
        "swap_free": swap_memory.free,
        "usage_percent": virtual_memory.percent,
    }

    # --------------------------------------------------------
    # Disk
    # --------------------------------------------------------

    disk_usage_total = 0
    disk_usage_used = 0
    disk_usage_free = 0

    try:
        partitions = psutil.disk_partitions(
            all=False
        )

        for partition in partitions:
            try:
                usage = psutil.disk_usage(
                    partition.mountpoint
                )

                disk_usage_total += usage.total
                disk_usage_used += usage.used
                disk_usage_free += usage.free

            except (
                PermissionError,
                OSError,
            ):
                continue

    except Exception:
        logger.exception(
            "Failed to collect Windows disk partitions"
        )

    disk_usage_percent = (
        (
            disk_usage_used
            / disk_usage_total
        ) * 100
        if disk_usage_total > 0
        else None
    )

    disk_io = psutil.disk_io_counters()

    disk_metrics: dict[str, Any] = {
        "usage_percent": disk_usage_percent,
        "total": disk_usage_total,
        "used": disk_usage_used,
        "free": disk_usage_free,
        "read_bytes_per_sec": None,
        "write_bytes_per_sec": None,
        "read_ops_per_sec": None,
        "write_ops_per_sec": None,
        "io_utilization_percent": None,
        "io_time_seconds_per_sec": None,
        "latency": {
            "read_ms": None,
            "write_ms": None,
        },
    }

    if disk_io:
        disk_metrics["read_bytes"] = disk_io.read_bytes
        disk_metrics["write_bytes"] = disk_io.write_bytes
        disk_metrics["read_count"] = disk_io.read_count
        disk_metrics["write_count"] = disk_io.write_count
        disk_metrics["read_time_ms"] = disk_io.read_time
        disk_metrics["write_time_ms"] = disk_io.write_time

    # --------------------------------------------------------
    # Filesystem
    # --------------------------------------------------------

    filesystems: list[dict[str, Any]] = []

    try:
        for partition in psutil.disk_partitions(
            all=False
        ):
            try:
                usage = psutil.disk_usage(
                    partition.mountpoint
                )

                filesystems.append(
                    {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "usage_percent": usage.percent,
                    }
                )

            except (
                PermissionError,
                OSError,
            ):
                continue

    except Exception:
        logger.exception(
            "Failed to collect Windows filesystem metrics"
        )

    filesystem_metrics: dict[str, Any] = {
        "filesystems": filesystems,
    }

    # --------------------------------------------------------
    # Network
    # --------------------------------------------------------

    network_io = psutil.net_io_counters(
        pernic=True
    )

    interfaces: list[dict[str, Any]] = []

    network_stats = psutil.net_if_stats()

    for interface_name, counters in network_io.items():

        stats = network_stats.get(
            interface_name
        )

        interfaces.append(
            {
                "interface": interface_name,
                "rx_bytes": counters.bytes_recv,
                "tx_bytes": counters.bytes_sent,
                "rx_packets": counters.packets_recv,
                "tx_packets": counters.packets_sent,
                "rx_errors": counters.errin,
                "tx_errors": counters.errout,
                "rx_dropped": counters.dropin,
                "tx_dropped": counters.dropout,
                "state": (
                    "UP"
                    if stats and stats.isup
                    else "DOWN"
                ),
            }
        )

    total_rx = sum(
        item.bytes_recv
        for item in network_io.values()
    )

    total_tx = sum(
        item.bytes_sent
        for item in network_io.values()
    )

    total_rx_packets = sum(
        item.packets_recv
        for item in network_io.values()
    )

    total_tx_packets = sum(
        item.packets_sent
        for item in network_io.values()
    )

    total_rx_errors = sum(
        item.errin
        for item in network_io.values()
    )

    total_tx_errors = sum(
        item.errout
        for item in network_io.values()
    )

    network_metrics: dict[str, Any] = {
        "rx_bytes_per_sec": None,
        "tx_bytes_per_sec": None,
        "rx_packets_per_sec": None,
        "tx_packets_per_sec": None,
        "rx_errors_per_sec": None,
        "tx_errors_per_sec": None,
        "dropped_packets_per_sec": {
            "rx": None,
            "tx": None,
        },
        "interfaces": interfaces,
        "total_rx_bytes": total_rx,
        "total_tx_bytes": total_tx,
        "total_rx_packets": total_rx_packets,
        "total_tx_packets": total_tx_packets,
        "total_rx_errors": total_rx_errors,
        "total_tx_errors": total_tx_errors,
    }

    # --------------------------------------------------------
    # Processes
    # --------------------------------------------------------

    running = 0
    sleeping = 0
    stopped = 0
    zombie = 0
    total_processes = 0

    top_cpu: list[dict[str, Any]] = []
    top_memory: list[dict[str, Any]] = []

    process_data: list[dict[str, Any]] = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "status",
            "cpu_percent",
            "memory_info",
        ],
        ad_value=None,
    ):
        try:
            info = process.info

            total_processes += 1

            status = str(
                info.get("status") or ""
            ).lower()

            if status == psutil.STATUS_RUNNING:
                running += 1

            elif status == psutil.STATUS_SLEEPING:
                sleeping += 1

            elif status == psutil.STATUS_STOPPED:
                stopped += 1

            elif status == psutil.STATUS_ZOMBIE:
                zombie += 1

            memory_info = info.get(
                "memory_info"
            )

            memory_bytes = (
                memory_info.rss
                if memory_info
                else 0
            )

            process_data.append(
                {
                    "process": info.get("name")
                    or "unknown",
                    "cpu": info.get(
                        "cpu_percent"
                    )
                    or 0.0,
                    "memory": memory_bytes,
                }
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
        ):
            continue

    top_cpu = [
        {
            "process": item["process"],
            "cpu_seconds_per_sec": item["cpu"],
        }
        for item in sorted(
            process_data,
            key=lambda item: item["cpu"],
            reverse=True,
        )[:5]
    ]

    top_memory = [
        {
            "process": item["process"],
            "memory_bytes": item["memory"],
        }
        for item in sorted(
            process_data,
            key=lambda item: item["memory"],
            reverse=True,
        )[:5]
    ]

    processes_metrics: dict[str, Any] = {
        "counts": {
            "total": total_processes,
            "running": running,
            "sleeping": sleeping,
            "stopped": stopped,
            "zombie": zombie,
            "blocked": None,
        },
        "top_by_cpu": top_cpu,
        "top_by_memory": top_memory,
    }

    # --------------------------------------------------------
    # System
    # --------------------------------------------------------

    boot_time = psutil.boot_time()

    uptime_seconds = (
        datetime.now(timezone.utc).timestamp()
        - boot_time
    )

    logical_cpu = psutil.cpu_count(
        logical=True
    )

    physical_cpu = psutil.cpu_count(
        logical=False
    )

    system_metrics: dict[str, Any] = {
        "hostname": platform.node(),
        "kernel_version": platform.version(),
        "os_version": platform.system(),
        "architecture": platform.machine(),
        "boot_time": boot_time,
        "uptime_seconds": uptime_seconds,
        "cpu_logical": logical_cpu,
        "cpu_cores": physical_cpu,
        "logged_users": None,
    }

    # --------------------------------------------------------
    # Sockets / network connections
    # --------------------------------------------------------

    tcp_connections = 0
    established_connections = 0
    time_wait = 0
    close_wait = 0

    try:
        connections = psutil.net_connections(
            kind="inet"
        )

        for connection in connections:

            if connection.type == 2:
                # UDP
                continue

            tcp_connections += 1

            status = str(
                connection.status or ""
            ).upper()

            if status == "ESTABLISHED":
                established_connections += 1

            elif status == "TIME_WAIT":
                time_wait += 1

            elif status == "CLOSE_WAIT":
                close_wait += 1

    except (
        psutil.AccessDenied,
        PermissionError,
    ):
        logger.warning(
            "Access denied while collecting Windows socket metrics"
        )

    socket_metrics: dict[str, Any] = {
        "tcp_connections": tcp_connections,
        "udp_sockets": None,
        "listening_sockets": None,
        "established_connections": established_connections,
        "time_wait": time_wait,
        "close_wait": close_wait,
    }

    # --------------------------------------------------------
    # Windows services
    # --------------------------------------------------------

    running_services = None
    failed_services = None
    active_services = None

    try:
        services = psutil.win_service_iter()

        running_services_count = 0
        active_services_count = 0

        for service in services:
            try:
                service_info = service.as_dict()

                status = str(
                    service_info.get("status")
                    or ""
                ).lower()

                if status == "running":
                    running_services_count += 1
                    active_services_count += 1

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                continue

        running_services = running_services_count
        active_services = active_services_count

    except (
        AttributeError,
        NotImplementedError,
    ):
        logger.warning(
            "Windows service collection is not available"
        )

    services_metrics: dict[str, Any] = {
        "running_services": running_services,
        "failed_services": failed_services,
        "active_services": active_services,
    }

    # --------------------------------------------------------
    # Prometheus
    #
    # Windows does not require Prometheus for collection.
    # We keep a compatible structure so the health analyzer
    # and report can consume the same payload.
    # --------------------------------------------------------

    prometheus_metrics: dict[str, Any] = {
        "availability": "NOT_USED",
        "targets": [],
        "scrape_duration_seconds": None,
        "scrape_success_percent": None,
    }

    logger.info(
        "Windows psutil collection completed"
    )

    return {
        "prometheus": prometheus_metrics,
        "cpu": cpu_metrics,
        "memory": memory_metrics,
        "disk": disk_metrics,
        "filesystem": filesystem_metrics,
        "network": network_metrics,
        "processes": processes_metrics,
        "system": system_metrics,
        "socket": socket_metrics,
        "services": services_metrics,
    }


# ============================================================
# Linux / Prometheus collection
# ============================================================

def collect_linux_metrics(
    settings: Settings,
    logger: logging.Logger,
) -> dict[str, Any]:
    """
    Collect infrastructure metrics from Linux through
    Prometheus + Node Exporter.
    """

    logger.info(
        "Collecting Linux infrastructure metrics using "
        "Prometheus + Node Exporter"
    )

    logger.info(
        "Connecting to Prometheus at %s",
        settings.prometheus_url,
    )

    client = PrometheusClient(
        settings.prometheus_url,
        timeout_seconds=settings.prometheus_timeout_seconds,
    )

    prometheus_collector = PrometheusCollector(
        client
    )

    cpu_collector = CPUCollector(client)
    memory_collector = MemoryCollector(client)
    disk_collector = DiskCollector(client)
    filesystem_collector = FilesystemCollector(client)
    network_collector = NetworkCollector(client)
    process_collector = ProcessCollector(client)
    system_collector = SystemCollector(client)
    socket_collector = SocketCollector(client)
    services_collector = ServicesCollector(client)

    metrics: dict[str, Any] = {
        "prometheus": prometheus_collector.collect(),
        "cpu": cpu_collector.collect(),
        "memory": memory_collector.collect(),
        "disk": disk_collector.collect(),
        "filesystem": filesystem_collector.collect(),
        "network": network_collector.collect(),
        "processes": process_collector.collect(),
        "system": system_collector.collect(),
        "socket": socket_collector.collect(),
        "services": services_collector.collect(),
    }

    logger.info(
        "Linux Prometheus collection completed"
    )

    return metrics


# ============================================================
# Main
# ============================================================

def main() -> int:
    """Program entry point."""

    settings = Settings.from_env()

    logger = setup_logging(settings)

    identity = settings.to_machine_identity()

    logger.info(
        "%s",
        identity.startup_banner(
            "infrastructure-agent",
            settings.rabbitmq_url,
        ),
    )

    args = parse_args()

    if not args.collect:
        print(
            "Use --collect to generate a health report."
        )
        return 0

    # --------------------------------------------------------
    # Determine OS
    # --------------------------------------------------------

    try:
        operating_system = detect_operating_system(
            settings
        )
    except Exception as exc:
        logger.exception(
            "Unable to determine operating system"
        )
        print(
            f"Collection failed: {exc}"
        )
        return 2

    logger.info(
        "Infrastructure agent operating system: %s",
        operating_system,
    )

    # --------------------------------------------------------
    # Collect metrics
    # --------------------------------------------------------

    try:

        logger.info(
            "Metric collection started | OS=%s | "
            "Tenant=%s | Machine=%s | Environment=%s",
            operating_system,
            settings.tenant_name,
            settings.machine_reference,
            settings.environment_name,
        )

        if operating_system == "LINUX":

            metrics = collect_linux_metrics(
                settings=settings,
                logger=logger,
            )

        elif operating_system == "WINDOWS":

            metrics = collect_windows_metrics(
                logger=logger,
            )

        else:
            raise RuntimeError(
                f"Unsupported operating system: "
                f"{operating_system}"
            )

    except PrometheusClientError as exc:

        logger.error(
            "Prometheus collection failed: %s",
            exc,
        )

        print(
            f"Collection failed: {exc}"
        )

        return 2

    except Exception as exc:

        logger.exception(
            "Unexpected collection failure"
        )

        print(
            f"Collection failed: {exc}"
        )

        return 2

    # --------------------------------------------------------
    # Analyze health
    # --------------------------------------------------------

    health_analyzer = HealthAnalyzer()

    report = health_analyzer.analyze(
        metrics
    )

    timestamp = datetime.now(
        timezone.utc
    )

    prometheus = metrics.get(
        "prometheus",
        {},
    )

    cpu = metrics.get(
        "cpu",
        {},
    )

    memory = metrics.get(
        "memory",
        {},
    )

    disk = metrics.get(
        "disk",
        {},
    )

    network = metrics.get(
        "network",
        {},
    )

    # --------------------------------------------------------
    # Build report
    # --------------------------------------------------------

    report_text = build_health_report_text(
        timestamp=timestamp,
        target=settings.target_name,
        metrics=metrics,
        health_report=report,
    )

    print(
        report_text,
        end="",
    )

    # --------------------------------------------------------
    # Save local report
    # --------------------------------------------------------

    try:

        save_latest_health_report(
            report_text
        )

    except Exception:

        logger.exception(
            "Failed to write the latest health report"
        )

        print(
            "Warning: failed to save "
            "reports/latest_health_report.txt"
        )

    # --------------------------------------------------------
    # Logging summary
    # --------------------------------------------------------

    logger.info(
        "Health analysis result: %s | Problems=%s",
        report.status,
        (
            "; ".join(report.problems)
            if report.problems
            else "none"
        ),
    )

    logger.info(
        "Metric collection completed | "
        "OS=%s | "
        "Availability=%s | "
        "CPU=%s | "
        "Memory=%s | "
        "Disk=%s | "
        "Network RX=%s | "
        "Network TX=%s",
        operating_system,
        prometheus.get(
            "availability",
            "NOT_USED",
        ),
        format_metric(
            cpu.get("overall_usage")
        ),
        format_metric(
            memory.get("usage_percent")
        ),
        format_metric(
            disk.get("usage_percent")
        ),
        format_network(
            network.get(
                "rx_bytes_per_sec"
            )
        ),
        format_network(
            network.get(
                "tx_bytes_per_sec"
            )
        ),
    )

    # --------------------------------------------------------
    # Publish to RabbitMQ
    # --------------------------------------------------------

    if settings.rabbitmq_url:

        from rabbitmq_publisher import (
            RabbitMqPublisher,
        )

        publish_payload = {
            "target": settings.target_name,
            "timestamp": timestamp.isoformat(),
            "status": report.status,
            "problems": report.problems,
            "operating_system": operating_system,
            "tenant": settings.tenant_name,
            "environment": settings.environment_name,
            "machine_reference": (
                settings.machine_reference
            ),
            "metrics": metrics,
        }

        publisher = RabbitMqPublisher(
            url=settings.rabbitmq_url
        )

        publisher.publish(
            agent_key="infrastructure",
            data=publish_payload,
            identity=identity,
        )

        logger.info(
            "Infrastructure metrics successfully "
            "published to RabbitMQ."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

