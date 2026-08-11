import psutil

class WindowsMemoryCollector:

    def collect(self) -> dict:
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "total": memory.total,
            "used": memory.used,
            "free": memory.free,
            "available": memory.available,
            "usage_percent": memory.percent,
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_free": swap.free,
        }