"""Custom exceptions for the DataDog HealthCheck Deployer."""


class DeployerError(Exception):
    """Base exception for all deployer errors."""

    def __init__(self, message: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
        """
        self.message = message
        super().__init__(self.message)


class ConfigError(DeployerError):
    """Exception raised for configuration errors."""

    pass


class ValidationError(DeployerError):
    """Exception raised for validation errors."""

    pass


class APIError(DeployerError):
    """Exception raised for DataDog API errors."""

    def __init__(self, message: str, status_code: int = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            status_code: HTTP status code
        """
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(APIError):
    """Exception raised for authentication errors."""

    pass


class RateLimitError(APIError):
    """Exception raised for rate limit errors."""

    def __init__(self, message: str, reset_time: int = None) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            reset_time: Rate limit reset time
        """
        self.reset_time = reset_time
        super().__init__(message)


class CheckError(DeployerError):
    """Exception raised for health check errors."""

    def __init__(self, message: str, check_name: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            check_name: Name of the health check
        """
        self.check_name = check_name
        super().__init__(f"Check {check_name}: {message}")


class MonitorError(DeployerError):
    """Exception raised for monitor errors."""

    def __init__(self, message: str, monitor_name: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            monitor_name: Name of the monitor
        """
        self.monitor_name = monitor_name
        super().__init__(f"Monitor {monitor_name}: {message}")


class DashboardError(DeployerError):
    """Exception raised for dashboard errors."""

    def __init__(self, message: str, dashboard_name: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            dashboard_name: Name of the dashboard
        """
        self.dashboard_name = dashboard_name
        super().__init__(f"Dashboard {dashboard_name}: {message}")


class TemplateError(ConfigError):
    """Exception raised for template errors."""

    def __init__(self, message: str, template_name: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            template_name: Name of the template
        """
        self.template_name = template_name
        super().__init__(f"Template {template_name}: {message}")


class VariableError(ConfigError):
    """Exception raised for variable errors."""

    def __init__(self, message: str, variable_name: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            variable_name: Name of the variable
        """
        self.variable_name = variable_name
        super().__init__(f"Variable {variable_name}: {message}")


class LocationError(DeployerError):
    """Exception raised for location errors."""

    def __init__(self, message: str, location: str) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            location: Name of the location
        """
        self.location = location
        super().__init__(f"Location {location}: {message}")


class TimeoutError(DeployerError):
    """Exception raised for timeout errors."""

    def __init__(self, message: str, timeout: int) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            timeout: Timeout value in seconds
        """
        self.timeout = timeout
        super().__init__(f"Timeout ({timeout}s): {message}")


class RetryError(DeployerError):
    """Exception raised for retry errors."""

    def __init__(self, message: str, attempts: int) -> None:
        """Initialize the exception.

        Args:
            message: Error message
            attempts: Number of retry attempts
        """
        self.attempts = attempts
        super().__init__(f"Retry failed after {attempts} attempts: {message}")


class ValidationWarning(Warning):
    """Warning raised for validation issues."""

    pass


class DeprecationWarning(Warning):
    """Warning raised for deprecated features."""

    pass
