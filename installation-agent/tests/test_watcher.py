import pytest
import time
from app.watchers.file_watcher import InstallerWatcher
from app.config.settings import settings

def test_watcher_lifecycle():
    watcher = InstallerWatcher()
    
    # Try starting and stopping watcher observer
    try:
        watcher.start()
        time.sleep(0.5)  # brief wait
        watcher.stop()
    except Exception as e:
        pytest.fail(f"Watcher observer lifecycle raised exception: {e}")
