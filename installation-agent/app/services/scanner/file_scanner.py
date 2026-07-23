import os
import hashlib
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
import getpass
from app.config.settings import settings
from app.models.schemas import FileMetadata, ScanResults

logger = logging.getLogger("installation_agent")

ENTRYPOINT_NAMES = {
    "install.sh", "setup.sh", "start.sh", "bootstrap.sh", "deploy.sh",
    "postinstall.sh", "preinstall.sh", "configure.sh",
    "install.ps1", "install.bat", "setup.exe", "installer.exe", "setup.msi"
}

INSTALLER_EXTENSIONS = {".msi", ".rpm", ".deb", ".bin"}

def calculate_hashes(file_path: Path) -> tuple[str, str]:
    """Calculates MD5 and SHA256 hashes of a file in chunks to optimize memory."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                md5.update(chunk)
                sha256.update(chunk)
        return md5.hexdigest(), sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hashes for {file_path}: {e}")
        return "", ""

class FileScanner:
    """Recursively scans target directory for artifacts and computes metadata."""
    def __init__(self, target_dir: Path | None = None):
        self.target_dir = target_dir or settings.get_absolute_path(settings.fake_files_dir)
        
    def scan(self) -> ScanResults:
        logger.info(f"Starting directory scan of target: {self.target_dir}")
        if not self.target_dir.exists():
            logger.warning(f"Target directory {self.target_dir} does not exist.")
            return ScanResults(
                timestamp=datetime.utcnow().isoformat() + "Z",
                total_files=0,
                total_size_bytes=0,
                files=[],
                duplicates={},
                entrypoints=[]
            )
            
        files_metadata = []
        hash_to_paths = {}
        entrypoints = []
        
        # Traverse recursively while ignoring specified directories
        for root, dirs, files in os.walk(self.target_dir, followlinks=settings.follow_symlinks):
            # Modify dirs in-place to avoid traversing ignored folders
            dirs[:] = [d for d in dirs if d not in settings.ignored_folders and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                
                # Check for symlink
                is_symlink = file_path.is_symlink()
                
                try:
                    stat_info = file_path.stat()
                except Exception as e:
                    logger.warning(f"Could not get file statistics for {file_path}: {e}")
                    continue
                
                size = stat_info.st_size
                created = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                modified = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                
                # Owner resolution (handle OS specifics)
                try:
                    owner = file_path.owner()
                except (NotImplementedError, KeyError, Exception):
                    owner = getpass.getuser()
                    
                # Permissions octal representation
                perms = oct(stat_info.st_mode & 0o777)
                
                # File hashes
                md5_hash, sha256_hash = calculate_hashes(file_path)
                
                # Guess mime type
                mime, _ = mimetypes.guess_type(file_path)
                if not mime:
                    mime = "application/octet-stream"
                    
                rel_path = file_path.relative_to(self.target_dir).as_posix()
                abs_path = file_path.resolve().as_posix()
                
                metadata = FileMetadata(
                    absolute_path=abs_path,
                    relative_path=rel_path,
                    filename=file,
                    extension=file_path.suffix.lower(),
                    size_bytes=size,
                    creation_date=created,
                    modification_date=modified,
                    sha256=sha256_hash,
                    md5=md5_hash,
                    mime_type=mime,
                    permissions=perms,
                    owner=owner,
                    is_symlink=is_symlink
                )
                files_metadata.append(metadata)
                
                if sha256_hash:
                    hash_to_paths.setdefault(sha256_hash, []).append(abs_path)
                    
                if file in ENTRYPOINT_NAMES or file_path.suffix.lower() in INSTALLER_EXTENSIONS:
                    entrypoints.append(abs_path)
                    
        # Filter out hashes that only have one occurrence (i.e. not duplicates)
        duplicates = {k: v for k, v in hash_to_paths.items() if len(v) > 1}
        total_size = sum(f.size_bytes for f in files_metadata)
        
        logger.info(f"Scan complete. Indexed {len(files_metadata)} files. Duplicates: {len(duplicates)}. Entrypoints: {len(entrypoints)}")
        
        return ScanResults(
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_files=len(files_metadata),
            total_size_bytes=total_size,
            files=files_metadata,
            duplicates=duplicates,
            entrypoints=entrypoints
        )
