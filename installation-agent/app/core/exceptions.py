class InstallationError(Exception):
    """Base exception for the Installation Agent."""
    pass

class ValidationError(InstallationError):
    """Exception raised when a file fails validation."""
    pass

class DependencyError(InstallationError):
    """Exception raised for dependency-related issues."""
    pass

class InstallationPermissionError(InstallationError):
    """Exception raised when permission issues are encountered during scanning or parsing."""
    pass

class FileCorruptedError(ValidationError):
    """Exception raised when an installer or configuration file is corrupted."""
    pass

class RollbackError(InstallationError):
    """Exception raised when rollback operations fail."""
    pass

class ConfigurationError(InstallationError):
    """Exception raised when configuration is invalid or missing."""
    pass
