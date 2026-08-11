import psutil

class WindowsDiskCollector:

    def collect(self) -> dict:
        total = 0
        used = 0
        free = 0

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue

            total += usage.total
            used += usage.used
            free += usage.free

        usage_percent = (
            (used / total) * 100
            if total > 0
            else None
        )

        return {
            "total": total,
            "used": used,
            "free": free,
            "usage_percent": usage_percent,
        }