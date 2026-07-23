import pytest
import shutil
from pathlib import Path
from app.config.settings import settings
from app.utils.fake_files_generator import FakeFilesGenerator

@pytest.fixture(scope="session", autouse=True)
def setup_test_files():
    """Session fixture that automatically builds the mock environment data in fake_files/."""
    test_dir = settings.get_absolute_path(settings.fake_files_dir)
    # Recreate the folder structure cleanly
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)
    
    FakeFilesGenerator.generate_all(test_dir)
    yield
    # We keep the directory for manual inspections and watcher validations
