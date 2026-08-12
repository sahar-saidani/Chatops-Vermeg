"""Shared, extensible file-type heuristics for the scan/analysis pipeline.

Used by both app/core/pipeline.py (decides whether to run ConfigParser on a
file) and app/services/analyzer/installation_metadata_collector.py (decides
whether a file is reported as a "configuration file"). Kept in one place so
the two stay consistent - a file recognized by one and missed by the other
would silently disappear from the published result.

Deliberately extension-*denylist* based rather than a fixed allowlist: real
deployments use custom extensions (e.g. Vermeg's `*.tokens` property files)
that a fixed list of ".env/.yaml/.json/..." would never anticipate. Any
file that isn't a known script or a known binary/media format is treated as
a configuration candidate and run through ConfigParser's structured parsers
plus its regex-based fallback parser for unrecognized formats.
"""

from __future__ import annotations

SCRIPT_EXTENSIONS = {".sh", ".ps1", ".bat", ".cmd", ".service"}

# Formats that are never configuration text, so running the config parser
# on them would only add noise (and cost, for large binaries).
NON_CONFIG_EXTENSIONS = {
    # executables / packages
    ".exe", ".msi", ".rpm", ".deb", ".bin", ".dll", ".so", ".dylib", ".class", ".jar", ".war",
    # archives
    ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar",
    # media / documents
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".svg", ".pdf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # noise / build artifacts
    ".pyc", ".pyo", ".log", ".lock",
}

_EXPLICIT_CONFIG_FILENAMES = {
    ".env",
    ".env.example",
    ".env.template",
    "web.config",
    "nginx.conf",
    "apache.conf",
    "application.properties",
    "environment.conf",
    "application.env.template",
}

_EXPLICIT_CONFIG_EXTENSIONS = {
    ".env", ".properties", ".yaml", ".yml", ".json", ".ini", ".xml", ".reg", ".conf", ".cfg", ".toml", ".config",
}


def is_probable_config_file(filename: str, extension: str) -> bool:
    """True if this file should be treated as configuration/installation
    metadata and run through ConfigParser.

    filename/extension are expected already lower-cased.
    """

    if filename in _EXPLICIT_CONFIG_FILENAMES or extension in _EXPLICIT_CONFIG_EXTENSIONS:
        return True

    if extension in SCRIPT_EXTENSIONS or extension in NON_CONFIG_EXTENSIONS:
        return False

    # Anything else (custom/unknown extension, or none at all - e.g. a
    # Vermeg *.tokens properties file, or a Dockerfile) is a candidate:
    # ConfigParser falls back to a generic key/value regex scan for
    # formats it doesn't specifically recognize.
    return True
