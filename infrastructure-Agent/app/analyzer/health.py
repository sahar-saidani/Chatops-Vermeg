"""Infrastructure health analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

HealthStatus = Literal[
    "HEALTHY",
    "WARNING",
    "CRITICAL",
]


@dataclass(slots=True)
class HealthReport:
    """Final infrastructure health assessment."""

    status: HealthStatus
    problems: list[str] = field(
        default_factory=list
    )
    recommendation: str = "No action required"

    def to_dict(
        self,
    ) -> dict[str, object]:
        """Return a plain Python representation."""

        return {
            "status": self.status,
            "problems": list(self.problems),
            "recommendation": self.recommendation,
        }


class HealthAnalyzer:
    """Analyze category metrics and produce a synthesized health report."""

    def analyze(
        self,
        metrics: dict[str, Any],
    ) -> HealthReport:
        """Evaluate the current health state from collected infrastructure metrics."""

        problems: list[str] = []
        recommendations: list[str] = []
        statuses: list[HealthStatus] = []

        # ============================================================
        # Prometheus
        # ============================================================

        prometheus = metrics.get(
            "prometheus",
            {},
        )

        availability = str(
            prometheus.get(
                "availability",
                "NOT_USED",
            )
        ).upper()

        # IMPORTANT:
        #
        # Windows/psutil sets Prometheus to NOT_USED.
        # NOT_USED is not an error.
        #
        # Only evaluate Prometheus health when Prometheus
        # is actually being used.

        if availability == "DOWN":

            statuses.append(
                "CRITICAL"
            )

            problems.append(
                "One or more Prometheus targets are DOWN"
            )

            recommendations.append(
                "Check Prometheus targets, Node Exporter service, "
                "and network connectivity."
            )

        elif availability not in {
            "UP",
            "NOT_USED",
        }:

            statuses.append(
                "WARNING"
            )

            problems.append(
                f"Unknown Prometheus availability state: "
                f"{availability}"
            )

            recommendations.append(
                "Verify Prometheus availability and configuration."
            )

        # ============================================================
        # CPU
        # ============================================================

        cpu = metrics.get(
            "cpu",
            {},
        )

        cpu_usage = self._as_float(
            cpu.get("overall_usage")
        )

        self._evaluate_threshold(
            value=cpu_usage,
            warning=70.0,
            critical=85.0,
            warning_problem="CPU usage is elevated",
            critical_problem="CPU usage is critically high",
            recommendation=(
                "Check CPU-intensive workloads "
                "and thread contention."
            ),
            statuses=statuses,
            problems=problems,
            recommendations=recommendations,
        )

        # ============================================================
        # Memory
        # ============================================================

        memory = metrics.get(
            "memory",
            {},
        )

        memory_usage = self._as_float(
            memory.get("usage_percent")
        )

        self._evaluate_threshold(
            value=memory_usage,
            warning=75.0,
            critical=90.0,
            warning_problem="Memory usage is elevated",
            critical_problem="Memory usage is critically high",
            recommendation=(
                "Inspect memory usage and reclaim pressure."
            ),
            statuses=statuses,
            problems=problems,
            recommendations=recommendations,
        )

        # ============================================================
        # Disk
        # ============================================================

        disk = metrics.get(
            "disk",
            {},
        )

        disk_usage = self._as_float(
            disk.get("usage_percent")
        )

        self._evaluate_threshold(
            value=disk_usage,
            warning=80.0,
            critical=90.0,
            warning_problem="Disk usage is elevated",
            critical_problem="Disk usage is critically high",
            recommendation=(
                "Free disk space and verify retention policies."
            ),
            statuses=statuses,
            problems=problems,
            recommendations=recommendations,
        )

        # ============================================================
        # Disk IO
        # ============================================================

        io_util = self._as_float(
            disk.get(
                "io_utilization_percent"
            )
        )

        if (
            io_util is not None
            and io_util >= 90.0
        ):

            statuses.append(
                "WARNING"
            )

            problems.append(
                "Disk IO utilization is very high"
            )

            recommendations.append(
                "Investigate IO bottlenecks and optimize "
                "disk-bound workloads."
            )

        # ============================================================
        # Filesystems
        # ============================================================

        filesystem_data = metrics.get(
            "filesystem",
            {},
        )

        filesystems = filesystem_data.get(
            "filesystems",
            [],
        )

        for fs in filesystems:

            usage = self._as_float(
                fs.get("usage_percent")
            )

            mountpoint = fs.get(
                "mountpoint",
                "unknown",
            )

            if usage is None:
                continue

            if usage > 90.0:

                statuses.append(
                    "CRITICAL"
                )

                problems.append(
                    f"Filesystem {mountpoint} "
                    "is above 90% usage"
                )

                recommendations.append(
                    "Clean up or extend filesystem capacity."
                )

            elif usage >= 80.0:

                statuses.append(
                    "WARNING"
                )

                problems.append(
                    f"Filesystem {mountpoint} "
                    "is above 80% usage"
                )

                recommendations.append(
                    "Monitor filesystem growth "
                    "and plan cleanup."
                )

        # ============================================================
        # Network
        # ============================================================

        network = metrics.get(
            "network",
            {},
        )

        rx_errors = self._as_float(
            network.get(
                "rx_errors_per_sec"
            )
        )

        tx_errors = self._as_float(
            network.get(
                "tx_errors_per_sec"
            )
        )

        dropped = network.get(
            "dropped_packets_per_sec",
            {},
        )

        dropped_rx = self._as_float(
            dropped.get("rx")
        )

        dropped_tx = self._as_float(
            dropped.get("tx")
        )

        if any(
            value is not None
            and value > 0.0
            for value in (
                rx_errors,
                tx_errors,
                dropped_rx,
                dropped_tx,
            )
        ):

            statuses.append(
                "WARNING"
            )

            problems.append(
                "Network interface errors "
                "or packet drops detected"
            )

            recommendations.append(
                "Inspect interface health, MTU, "
                "and link stability."
            )

        # ============================================================
        # Processes
        # ============================================================

        processes = metrics.get(
            "processes",
            {},
        ).get(
            "counts",
            {},
        )

        zombie = self._as_float(
            processes.get("zombie")
        )

        blocked = self._as_float(
            processes.get("blocked")
        )

        if (
            zombie is not None
            and zombie > 0
        ):

            statuses.append(
                "WARNING"
            )

            problems.append(
                "Zombie processes detected"
            )

            recommendations.append(
                "Identify parent processes "
                "and restart affected services."
            )

        if (
            blocked is not None
            and blocked > 10
        ):

            statuses.append(
                "WARNING"
            )

            problems.append(
                "High number of blocked "
                "processes detected"
            )

            recommendations.append(
                "Check storage or synchronization bottlenecks."
            )

        # ============================================================
        # Services
        # ============================================================

        services = metrics.get(
            "services",
            {},
        )

        failed_services = self._as_float(
            services.get(
                "failed_services"
            )
        )

        if (
            failed_services is not None
            and failed_services > 0
        ):

            statuses.append(
                "CRITICAL"
            )

            problems.append(
                "One or more services are in failed state"
            )

            recommendations.append(
                "Review failed services and restart "
                "or remediate them."
            )

        # ============================================================
        # Prometheus scrape duration
        #
        # Only relevant when Prometheus is actually used.
        # ============================================================

        if availability in {
            "UP",
            "DOWN",
        }:

            scrape_duration = self._as_float(
                prometheus.get(
                    "scrape_duration_seconds"
                )
            )

            if (
                scrape_duration is not None
                and scrape_duration > 5.0
            ):

                statuses.append(
                    "WARNING"
                )

                problems.append(
                    "Prometheus scrape duration is high"
                )

                recommendations.append(
                    "Check exporter and Prometheus performance."
                )

        # ============================================================
        # Essential metrics
        #
        # These are required for both Windows and Linux because
        # both collection paths provide CPU, memory and disk.
        # ============================================================

        essential_checks = {
            "cpu.overall_usage": cpu_usage,
            "memory.usage_percent": memory_usage,
            "disk.usage_percent": disk_usage,
        }

        missing = [
            name
            for name, value
            in essential_checks.items()
            if value is None
        ]

        if missing:

            statuses.append(
                "WARNING"
            )

            problems.append(
                "Missing essential metrics: "
                + ", ".join(missing)
            )

            recommendations.append(
                "Verify the infrastructure metric collection."
            )

        # ============================================================
        # Final result
        # ============================================================

        if not problems:

            return HealthReport(
                status="HEALTHY",
                problems=[],
                recommendation="No action required",
            )

        return HealthReport(
            status=self._overall_status(
                statuses
            ),
            problems=self._deduplicate(
                problems
            ),
            recommendation=self._join_recommendations(
                recommendations
            ),
        )

    # ============================================================
    # THRESHOLDS
    # ============================================================

    def _evaluate_threshold(
        self,
        *,
        value: float | None,
        warning: float,
        critical: float,
        warning_problem: str,
        critical_problem: str,
        recommendation: str,
        statuses: list[HealthStatus],
        problems: list[str],
        recommendations: list[str],
    ) -> None:
        """Apply a threshold policy to a metric value."""

        # Missing metrics should not automatically become CRITICAL.
        # The missing-metric check is handled separately.
        if value is None:
            return

        status = self._classify_metric(
            value,
            warning,
            critical,
        )

        if status == "HEALTHY":
            return

        statuses.append(
            status
        )

        problems.append(
            critical_problem
            if status == "CRITICAL"
            else warning_problem
        )

        recommendations.append(
            recommendation
        )

    # ============================================================
    # CLASSIFICATION
    # ============================================================

    @staticmethod
    def _classify_metric(
        value: float | None,
        warning_threshold: float,
        critical_threshold: float,
    ) -> HealthStatus:

        if value is None:
            return "WARNING"

        if value > critical_threshold:
            return "CRITICAL"

        if value >= warning_threshold:
            return "WARNING"

        return "HEALTHY"

    @staticmethod
    def _overall_status(
        statuses: list[HealthStatus],
    ) -> HealthStatus:

        if any(
            status == "CRITICAL"
            for status in statuses
        ):
            return "CRITICAL"

        if any(
            status == "WARNING"
            for status in statuses
        ):
            return "WARNING"

        return "HEALTHY"

    @staticmethod
    def _join_recommendations(
        recommendations: list[str],
    ) -> str:

        unique_recommendations: list[str] = []

        for recommendation in recommendations:

            if recommendation not in unique_recommendations:
                unique_recommendations.append(
                    recommendation
                )

        return (
            " ".join(unique_recommendations)
            if unique_recommendations
            else "No action required"
        )

    @staticmethod
    def _deduplicate(
        items: list[str],
    ) -> list[str]:

        seen: set[str] = set()
        unique: list[str] = []

        for item in items:

            if item in seen:
                continue

            seen.add(item)
            unique.append(item)

        return unique

    @staticmethod
    def _as_float(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None