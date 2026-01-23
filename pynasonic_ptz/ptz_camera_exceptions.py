"""
Custom exceptions for PTZ Camera operations.

This module defines exceptions used throughout the PTZ Camera library
for handling various error conditions during camera control operations.
"""


class PTZCameraError(Exception):
    """Base exception for all PTZ Camera errors."""
    pass


class CommandFailed(PTZCameraError):
    """Raised when a camera command fails to execute or receive a response."""
    
    def __init__(self, command: str, address: str, status_code: int = None, details: str = None):
        """
        Initialize CommandFailed exception.
        
        Args:
            command: The command that failed
            address: The camera address that was targeted
            status_code: HTTP status code if applicable
            details: Additional error details
        """
        self.command = command
        self.address = address
        self.status_code = status_code
        self.details = details
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with all available information."""
        msg = f"Command '{self.command}' failed for camera at {self.address}"
        if self.status_code:
            msg += f" (HTTP {self.status_code})"
        if self.details:
            msg += f": {self.details}"
        return msg


class InvalidParameter(PTZCameraError):
    """Raised when an invalid parameter is provided to a camera command."""
    
    def __init__(self, command: str, param_name: str, value, valid_range=None):
        """
        Initialize InvalidParameter exception.
        
        Args:
            command: The command that received the invalid parameter
            param_name: Name of the invalid parameter
            value: The invalid value that was provided
            valid_range: Optional tuple/description of valid values
        """
        self.command = command
        self.param_name = param_name
        self.value = value
        self.valid_range = valid_range
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with all available information."""
        msg = f"Invalid parameter '{self.param_name}' for command '{self.command}': {self.value}"
        if self.valid_range:
            msg += f" (valid range: {self.valid_range})"
        return msg


class InvalidCamera(PTZCameraError):
    """Raised when an unsupported or unknown camera model is specified."""
    
    def __init__(self, camera_model: str, available_models: list = None):
        """
        Initialize InvalidCamera exception.
        
        Args:
            camera_model: The invalid camera model that was specified
            available_models: Optional list of valid camera models
        """
        self.camera_model = camera_model
        self.available_models = available_models
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with all available information."""
        msg = f"'{self.camera_model}' is not a valid or tested camera model"
        if self.available_models:
            models = ", ".join(self.available_models)
            msg += f". Available models: {models}"
        else:
            msg += ". Please check cameras.py for valid camera models"
        return msg


class NetworkError(PTZCameraError):
    """Raised when a network-related error occurs."""
    
    def __init__(self, address: str, details: str = None):
        """
        Initialize NetworkError exception.
        
        Args:
            address: The camera address that was unreachable
            details: Additional error details
        """
        self.address = address
        self.details = details
        msg = f"Network error communicating with camera at {address}"
        if details:
            msg += f": {details}"
        super().__init__(msg)


class TimeoutError(PTZCameraError):
    """Raised when a camera command times out."""
    
    def __init__(self, command: str, address: str, timeout: float):
        """
        Initialize TimeoutError exception.
        
        Args:
            command: The command that timed out
            address: The camera address
            timeout: The timeout duration in seconds
        """
        self.command = command
        self.address = address
        self.timeout = timeout
        msg = f"Command '{command}' timed out after {timeout}s for camera at {address}"
        super().__init__(msg)