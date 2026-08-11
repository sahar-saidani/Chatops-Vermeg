import platform
import psutil
import socket

class WindowsSystemCollector:

    def collect(self) -> dict:

        boot_time = psutil.boot_time()

        return {
            "hostname": socket.gethostname(),
            "os_version": platform.platform(),
            "architecture": platform.machine(),
            "boot_time": boot_time,
            "uptime_seconds": (
                __import__("time").time() - boot_time
            ),
            "cpu_logical": psutil.cpu_count(logical=True),
            "cpu_cores": psutil.cpu_count(logical=False),
        }