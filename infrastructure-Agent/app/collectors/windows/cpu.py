import psutil

class WindowsCPUCollector:

    def collect(self) -> dict:
        return {
            "overall_usage": psutil.cpu_percent(interval=1),
            "logical_cpus": psutil.cpu_count(logical=True),
            "physical_cpus": psutil.cpu_count(logical=False),
            "load": None,
        }