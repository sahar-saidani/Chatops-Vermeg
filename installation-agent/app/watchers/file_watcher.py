import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.config.settings import settings
from app.core.pipeline import run_analysis_pipeline
from app.watchers.event_store import record_watchdog_event

logger = logging.getLogger("installation_agent")

class InstallerFileHandler(FileSystemEventHandler):
    """Event handler for Watchdog file events."""
    
    def __init__(self, watch_dir: Path):
        super().__init__()
        self.watch_dir = watch_dir
        self.last_triggered = 0.0
        self.cooldown = 1.0  # 1 second debounce window

    def _trigger_analysis(self, event_type: str, path: str):
        # Prevent rapid double-firings by filtering with a debounce cooldown
        now = time.time()
        if now - self.last_triggered < self.cooldown:
            return
        self.last_triggered = now
        
        logger.info(f"Watcher Alert: File {event_type} - {path}. Initiating automatic discovery scanner...")
        try:
            run_analysis_pipeline(self.watch_dir)
        except Exception as e:
            logger.error(f"Failed executing automated analysis: {e}")

    def _record_event(self, event_type: str, path: str, is_directory: bool = False):
        record_watchdog_event(event_type=event_type, path=path, is_directory=is_directory)

    def on_created(self, event):
        self._record_event("created", event.src_path, event.is_directory)
        if not event.is_directory:
            self._trigger_analysis("CREATED", event.src_path)

    def on_modified(self, event):
        self._record_event("modified", event.src_path, event.is_directory)
        if not event.is_directory:
            # Ignore modifications inside logs or reports if they share the directory structure
            if "logs" in event.src_path or "reports" in event.src_path:
                return
            self._trigger_analysis("MODIFIED", event.src_path)

    def on_deleted(self, event):
        self._record_event("deleted", event.src_path, event.is_directory)
        if not event.is_directory:
            self._trigger_analysis("DELETED", event.src_path)

    def on_created_directory(self, event):
        self._record_event("directory_created", event.src_path, True)

    def on_deleted_directory(self, event):
        self._record_event("directory_deleted", event.src_path, True)

    def on_moved(self, event):
        target_path = event.dest_path or event.src_path
        self._record_event("moved", target_path, event.is_directory)
        if not event.is_directory:
            self._trigger_analysis("MOVED/RENAMED", target_path)

class InstallerWatcher:
    """Wrapper class managing the watchdog observer lifecycle."""
    
    def __init__(self, watch_dir: Path | None = None):
        self.watch_dir = watch_dir or settings.get_absolute_path(settings.watch_directory)
        self.observer = Observer()
        
    def start(self):
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        event_handler = InstallerFileHandler(self.watch_dir)
        self.observer.schedule(event_handler, path=str(self.watch_dir), recursive=True)
        self.observer.start()
        logger.info(f"Directory Watchdog active. Monitoring folder: [underline]{self.watch_dir}[/underline]")
        
    def stop(self):
        self.observer.stop()
        self.observer.join()
        logger.info("Directory Watchdog observer shutdown completed.")
