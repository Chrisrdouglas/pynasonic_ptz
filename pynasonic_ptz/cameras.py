"""
Camera configuration database for PTZ cameras.

This module contains specifications for different PTZ camera models,
including their movement ranges, speed limits, and timing characteristics.
"""

from typing import TypedDict, Tuple


class AxisConfig(TypedDict):
    """Configuration for a single axis (pan or tilt)."""
    angles: Tuple[int, int]  # Min/max angles in degrees
    bounds: Tuple[int, int]  # Min/max raw position values
    max_speed: int  # Maximum speed in degrees/second
    speed_bounds: Tuple[int, int]  # Min/max speed values


class CameraConfig(TypedDict):
    """Complete configuration for a camera model."""
    pan: AxisConfig
    tilt: AxisConfig
    delay: float  # Command delay in seconds


# Camera specifications database
CAMERAS: dict[str, CameraConfig] = {
    "AW-HN40": {
        "pan": {
            "angles": (-30, 210),
            "bounds": (11529, 54005),
            "max_speed": 90,  # degrees/second
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 90),
            "bounds": (21845, 36408),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "delay": 0.13
    },
    "AW-UE150": {
        "pan": {
            "angles": (-175, 175),
            "bounds": (11529, 54005),
            "max_speed": 180,
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 210),
            "bounds": (7281, 36408),
            "max_speed": 180,
            "speed_bounds": (1, 100)
        },
        "delay": 0.04
    },
    "default": {
        "pan": {
            "angles": (-175, 175),
            "bounds": (0, 65535),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 90),
            "bounds": (0, 65535),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "delay": 0.13
    }
}


def get_camera_config(model: str, use_default_fallback: bool = True) -> CameraConfig:
    """
    Get configuration for a specific camera model.
    
    Args:
        model: Camera model identifier
        use_default_fallback: If True, return default config for unknown models
        
    Returns:
        Camera configuration dictionary
        
    Raises:
        KeyError: If model not found and use_default_fallback is False
    """
    if model in CAMERAS:
        return CAMERAS[model]
    
    if use_default_fallback:
        return CAMERAS["default"]
    
    raise KeyError(f"Camera model '{model}' not found in configuration")


def get_available_models() -> list[str]:
    """
    Get list of all configured camera models (excluding 'default').
    
    Returns:
        List of camera model names
    """
    return [model for model in CAMERAS.keys() if model != "default"]