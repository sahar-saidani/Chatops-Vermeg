from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class JsonLinesWriter:
    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path(__file__).resolve().parent.parent

    def write_json_lines(self, path: str | Path, items: Iterable[dict[str, Any]]) -> Path:
        resolved = self._resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("w", encoding="utf-8") as handle:
            for item in items:
                handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
                handle.write("\n")
        return resolved

    def write_json_document(self, path: str | Path, items: Iterable[dict[str, Any]]) -> Path:
        resolved = self._resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("w", encoding="utf-8") as handle:
            json.dump(list(items), handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        return resolved

    def _resolve_path(self, path: str | Path) -> Path:
        candidate = Path(path)
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            fallback = self._repo_root / "output" / candidate.name
            fallback.parent.mkdir(parents=True, exist_ok=True)
            return fallback
