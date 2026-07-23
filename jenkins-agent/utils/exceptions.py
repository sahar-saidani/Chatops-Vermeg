"""Custom exceptions for Jenkins agent."""


class JenkinsAgentError(Exception):
    """Base exception for Jenkins agent errors."""


class JenkinsConfigurationError(JenkinsAgentError):
    """Raised when required configuration is missing or invalid."""


class JenkinsHTTPError(JenkinsAgentError):
    """Raised when Jenkins API returns an HTTP error."""


class JenkinsTimeoutError(JenkinsAgentError):
    """Raised when a Jenkins API call times out."""
