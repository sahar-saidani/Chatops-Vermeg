import psutil

class WindowsProcessCollector:

    def collect(self) -> dict:

        processes = []

        for process in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_info"]
        ):
            try:
                info = process.info

                processes.append({
                    "pid": info["pid"],
                    "process": info["name"],
                    "cpu_percent": info["cpu_percent"],
                    "memory_bytes": (
                        info["memory_info"].rss
                        if info["memory_info"]
                        else None
                    ),
                })

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                continue

        processes.sort(
            key=lambda x: x["cpu_percent"] or 0,
            reverse=True
        )

        return {
            "total": len(processes),
            "top_by_cpu": processes[:5],
        }