"""
Pynasonic PTZ - Python library for controlling Panasonic PTZ cameras.

This package provides a simple interface for controlling Panasonic PTZ cameras
via their HTTP API, with support for multiple camera models.

Basic usage:
    >>> from pynasonic_ptz import PTZCamera
    >>> with PTZCamera(address="192.168.0.10") as camera:
    ...     camera.set_power_state(True)
    ...     camera.move_to_preset(5)
    ...     position = camera.get_pan_tilt_position()
"""

from .ptz_camera import PTZCamera
from .ptz_camera_exceptions import (
    PTZCameraError,
    CommandFailed,
    InvalidParameter,
    InvalidCamera,
    NetworkError,
    TimeoutError,
)
from .cameras import CAMERAS, get_camera_config, get_available_models

__version__ = "0.0.1"
__author__ = "Chris Douglas"
__all__ = [
    # Main class
    "PTZCamera",
    # Exceptions
    "PTZCameraError",
    "CommandFailed",
    "InvalidParameter",
    "InvalidCamera",
    "NetworkError",
    "TimeoutError",
    # Configuration helpers
    "CAMERAS",
    "get_camera_config",
    "get_available_models",
]