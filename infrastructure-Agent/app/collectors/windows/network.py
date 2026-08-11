import psutil

class WindowsNetworkCollector:

    def collect(self) -> dict:
        counters = psutil.net_io_counters()

        return {
            "bytes_sent": counters.bytes_sent,
            "bytes_received": counters.bytes_recv,
            "packets_sent": counters.packets_sent,
            "packets_received": counters.packets_recv,
            "errors_in": counters.errin,
            "errors_out": counters.errout,
            "dropped_in": counters.dropin,
            "dropped_out": counters.dropout,
        }