"""
PTZ Camera Control Library

This module provides a Python interface for controlling Pan-Tilt-Zoom (PTZ) cameras
via their HTTP API. It supports multiple camera models with model-specific configurations.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Literal
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .ptz_camera_exceptions import (
    CommandFailed, InvalidParameter, InvalidCamera, 
    NetworkError, TimeoutError
)
from .cameras import get_camera_config, get_available_models


# Constants
DEFAULT_TIMEOUT = 5.0  # seconds
DEFAULT_RETRY_ATTEMPTS = 3
ZOOM_LOWER_BOUND = 1365
ZOOM_UPPER_BOUND = 4096
PRESET_LOWER_BOUND = 0
PRESET_UPPER_BOUND = 100
MAX_POSITION_SPEED = 30


class PowerState(Enum):
    """Camera power states."""
    ON = "On"
    STANDBY = "Standby"
    TRANSITIONING = "Transitioning"
    OFF = "Off"


@dataclass
class AxisBounds:
    """Bounds for a camera axis (pan or tilt)."""
    angle_min: int
    angle_max: int
    position_min: int
    position_max: int
    speed_min: int
    speed_max: int
    max_speed: int


class PTZCamera:
    """
    Interface for controlling PTZ cameras via HTTP API.
    
    This class provides methods to control pan, tilt, zoom, focus, and other
    camera functions for supported Panasonic PTZ camera models.
    """

    def __init__(
        self,
        camera: str = "AW-HN40",
        address: str = "192.168.0.10",
        protocol: Literal["http", "https"] = "http",
        timeout: float = DEFAULT_TIMEOUT,
        retry_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        use_default_on_unknown: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize PTZ Camera controller.

        Args:
            camera: Camera model name (e.g., 'AW-HN40', 'AW-UE150')
            address: IP address or hostname of the camera
            protocol: Connection protocol ('http' or 'https')
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
            use_default_on_unknown: Use default config for unknown cameras
            logger: Optional logger instance for debugging

        Raises:
            InvalidCamera: If camera model is unknown and use_default_on_unknown is False
        """
        self.camera = camera
        self.address = address
        self.timeout = timeout
        self.logger = logger or logging.getLogger(__name__)
        
        # Build command URL template
        self.command_string = (
            f"{protocol}://{address}/cgi-bin/aw_ptz?cmd=%23{{cmd}}&res=1"
        )
        
        # Configure HTTP session with retry logic
        self.session = self._create_session(retry_attempts)
        
        # Load camera configuration
        try:
            cam_config = get_camera_config(camera, use_default_fallback=use_default_on_unknown)
            if camera not in get_available_models() and use_default_on_unknown:
                self.logger.warning(
                    f"Camera model '{camera}' not found. Using default configuration."
                )
        except KeyError:
            raise InvalidCamera(camera, get_available_models())
        
        # Set up axis bounds
        self.pan = AxisBounds(
            angle_min=cam_config['pan']['angles'][0],
            angle_max=cam_config['pan']['angles'][1],
            position_min=cam_config['pan']['bounds'][0],
            position_max=cam_config['pan']['bounds'][1],
            speed_min=cam_config['pan']['speed_bounds'][0],
            speed_max=cam_config['pan']['speed_bounds'][1],
            max_speed=cam_config['pan']['max_speed']
        )
        
        self.tilt = AxisBounds(
            angle_min=cam_config['tilt']['angles'][0],
            angle_max=cam_config['tilt']['angles'][1],
            position_min=cam_config['tilt']['bounds'][0],
            position_max=cam_config['tilt']['bounds'][1],
            speed_min=cam_config['tilt']['speed_bounds'][0],
            speed_max=cam_config['tilt']['speed_bounds'][1],
            max_speed=cam_config['tilt']['max_speed']
        )
        
        self.delay = cam_config['delay']
        
        # Zoom bounds
        self.zoom_min = ZOOM_LOWER_BOUND
        self.zoom_max = ZOOM_UPPER_BOUND
        
        # Preset bounds
        self.preset_min = PRESET_LOWER_BOUND
        self.preset_max = PRESET_UPPER_BOUND

    def _create_session(self, retry_attempts: int) -> requests.Session:
        """
        Create a requests session with retry logic.
        
        Args:
            retry_attempts: Number of retry attempts
            
        Returns:
            Configured requests Session
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _execute_command(
        self,
        command_name: str,
        cmd: str,
        response_pattern: str,
        responses: dict[str, any],
        default: any
    ) -> any:
        """
        Execute a camera command and parse the response.
        
        Args:
            command_name: Name of the command for error reporting
            cmd: Full command URL
            response_pattern: Regex pattern to validate response
            responses: Map of response strings to return values
            default: Default value if response doesn't match
            
        Returns:
            Parsed response value
            
        Raises:
            CommandFailed: If command execution fails
            NetworkError: If network communication fails
            TimeoutError: If request times out
        """
        try:
            self.logger.debug(f"Executing command: {command_name}")
            response = self.session.get(cmd, timeout=self.timeout)
            
            if response.status_code != 200:
                raise CommandFailed(
                    command_name, 
                    self.address, 
                    status_code=response.status_code
                )
            
            match = re.match(response_pattern, response.text)
            if match is None:
                raise CommandFailed(
                    command_name,
                    self.address,
                    details=f"Response '{response.text}' doesn't match pattern '{response_pattern}'"
                )
            
            return responses.get(response.text, default)
            
        except requests.exceptions.Timeout:
            raise TimeoutError(command_name, self.address, self.timeout)
        except requests.exceptions.RequestException as e:
            raise NetworkError(self.address, str(e))

    def _execute_query_command(
        self,
        command_name: str,
        cmd: str,
        default: any = None
    ) -> str:
        """
        Execute a query command and return the raw response.
        
        Args:
            command_name: Name of the command for error reporting
            cmd: Full command URL
            default: Default value if request fails
            
        Returns:
            Raw response text
            
        Raises:
            CommandFailed: If command execution fails
            NetworkError: If network communication fails
            TimeoutError: If request times out
        """
        try:
            self.logger.debug(f"Executing query: {command_name}")
            response = self.session.get(cmd, timeout=self.timeout)
            
            if response.status_code != 200:
                raise CommandFailed(
                    command_name,
                    self.address,
                    status_code=response.status_code
                )
            
            return response.text
            
        except requests.exceptions.Timeout:
            raise TimeoutError(command_name, self.address, self.timeout)
        except requests.exceptions.RequestException as e:
            raise NetworkError(self.address, str(e))

    @staticmethod
    def _zero_pad(value: str, desired_length: int) -> str:
        """
        Zero-pad a string to desired length.
        
        Args:
            value: String to pad
            desired_length: Target length
            
        Returns:
            Zero-padded string
        """
        return value.zfill(desired_length)

    @staticmethod
    def _format_hex(value: int, length: int) -> str:
        """
        Format integer as zero-padded uppercase hex string.
        
        Args:
            value: Integer value
            length: Desired string length
            
        Returns:
            Formatted hex string
        """
        hex_str = hex(value)[2:]  # Remove '0x' prefix
        return hex_str.zfill(length).upper()

    def _validate_range(
        self,
        value: any,
        min_val: int,
        max_val: int,
        param_name: str,
        command_name: str
    ) -> None:
        """
        Validate that a value is within an acceptable range.
        
        Args:
            value: Value to validate
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            param_name: Parameter name for error reporting
            command_name: Command name for error reporting
            
        Raises:
            InvalidParameter: If value is out of range
        """
        if not isinstance(value, int) or not (min_val <= value < max_val):
            raise InvalidParameter(
                command_name,
                param_name,
                value,
                valid_range=(min_val, max_val - 1)
            )

    # Properties
    @property
    def tilt_angle_range(self) -> Tuple[int, int]:
        """Get the tilt angle range in degrees."""
        return (self.tilt.angle_min, self.tilt.angle_max)

    @property
    def pan_angle_range(self) -> Tuple[int, int]:
        """Get the pan angle range in degrees."""
        return (self.pan.angle_min, self.pan.angle_max)

    @property
    def power_states(self) -> Tuple[str, ...]:
        """Get available power state values."""
        return tuple(state.value for state in PowerState)

    @property
    def preset_bounds(self) -> Tuple[int, int]:
        """Get the preset index bounds."""
        return (self.preset_min, self.preset_max - 1)

    @property
    def pan_bounds(self) -> Tuple[int, int]:
        """Get the pan position bounds."""
        return (self.pan.position_min, self.pan.position_max - 1)

    @property
    def pan_speed_bounds(self) -> Tuple[int, int]:
        """Get the pan speed bounds."""
        return (self.pan.speed_min, self.pan.speed_max - 1)

    @property
    def tilt_bounds(self) -> Tuple[int, int]:
        """Get the tilt position bounds."""
        return (self.tilt.position_min, self.tilt.position_max - 1)

    @property
    def tilt_speed_bounds(self) -> Tuple[int, int]:
        """Get the tilt speed bounds."""
        return (self.tilt.speed_min, self.tilt.speed_max - 1)

    @property
    def zoom_bounds(self) -> Tuple[int, int]:
        """Get the zoom bounds."""
        return (self.zoom_min, self.zoom_max - 1)

    # Camera control methods
    def get_power_state(self) -> str:
        """
        Read the current power state of the camera.

        Returns:
            Power state string ('On', 'Standby', 'Transitioning', or 'Off')
            
        Raises:
            CommandFailed: If command fails
        """
        url_cmd = self.command_string.format(cmd="O")
        responses = {
            'p0': PowerState.STANDBY.value,
            'p1': PowerState.ON.value,
            'p3': PowerState.TRANSITIONING.value
        }
        return self._execute_command(
            command_name="get_power_state",
            cmd=url_cmd,
            response_pattern=r"^p(\d)$",
            responses=responses,
            default=PowerState.OFF.value
        )

    def set_power_state(self, power_on: bool) -> str:
        """
        Set the power state of the camera.

        Args:
            power_on: True to power on, False for standby

        Returns:
            Resulting power state string
            
        Raises:
            CommandFailed: If command fails
        """
        state_value = "1" if power_on else "0"
        cmd = f"O{state_value}"
        url_cmd = self.command_string.format(cmd=cmd)
        responses = {
            'p0': PowerState.STANDBY.value,
            'p1': PowerState.ON.value,
            'p2': PowerState.TRANSITIONING.value
        }
        return self._execute_command(
            command_name="set_power_state",
            cmd=url_cmd,
            response_pattern=r"^p(\d)$",
            responses=responses,
            default=PowerState.OFF.value
        )

    def set_pan_tilt_speed(self, pan_speed: int, tilt_speed: int) -> bool:
        """
        Set the pan and tilt movement speeds.

        Args:
            pan_speed: Pan speed value (can be negative for reverse)
            tilt_speed: Tilt speed value (can be negative for reverse)

        Returns:
            True if successful, False otherwise
            
        Raises:
            InvalidParameter: If speeds are out of valid range
        """
        # Validate speed ranges (allowing negative values)
        if not (-self.pan.speed_max < pan_speed < self.pan.speed_max):
            raise InvalidParameter(
                "set_pan_tilt_speed",
                "pan_speed",
                pan_speed,
                valid_range=(-self.pan.speed_max + 1, self.pan.speed_max - 1)
            )
        if not (-self.tilt.speed_max < tilt_speed < self.tilt.speed_max):
            raise InvalidParameter(
                "set_pan_tilt_speed",
                "tilt_speed",
                tilt_speed,
                valid_range=(-self.tilt.speed_max + 1, self.tilt.speed_max - 1)
            )

        pan_str = self._zero_pad(str(pan_speed), 2)
        tilt_str = self._zero_pad(str(tilt_speed), 2)

        cmd = f"PTS{pan_str}{tilt_str}"
        url_cmd = self.command_string.format(cmd=cmd)
        response = f"pTS{pan_str}{tilt_str}"
        
        return self._execute_command(
            command_name="set_pan_tilt_speed",
            cmd=url_cmd,
            response_pattern=f"^{response}$",
            responses={response: True},
            default=False
        )

    def move_to_preset(self, preset_index: int) -> bool:
        """
        Move camera to a registered preset position.

        Args:
            preset_index: Preset index (0-99)

        Returns:
            True if command successful, False otherwise
            
        Raises:
            InvalidParameter: If preset_index is invalid
        """
        self._validate_range(
            preset_index,
            self.preset_min,
            self.preset_max,
            "preset_index",
            "move_to_preset"
        )

        preset_str = self._zero_pad(str(preset_index), 2)
        cmd = f"R{preset_str}"
        url_cmd = self.command_string.format(cmd=cmd)
        response = f"r{preset_str}"
        
        return self._execute_command(
            command_name="move_to_preset",
            cmd=url_cmd,
            response_pattern=f"^{response}$",
            responses={response: True},
            default=False
        )

    def set_pan_tilt_position(
        self,
        pan: int,
        tilt: int,
        speed: int,
        select: Literal[0, 2] = 0
    ) -> bool:
        """
        Move camera to absolute pan/tilt position.

        Args:
            pan: Pan position value
            tilt: Tilt position value
            speed: Movement speed (0-29)
            select: Speed mode (0=slow, 2=fast)

        Returns:
            True if command successful, False otherwise
            
        Raises:
            InvalidParameter: If any parameter is invalid
        """
        # Validate parameters
        self._validate_range(
            pan,
            self.pan.position_min,
            self.pan.position_max,
            "pan",
            "set_pan_tilt_position"
        )
        self._validate_range(
            tilt,
            self.tilt.position_min,
            self.tilt.position_max,
            "tilt",
            "set_pan_tilt_position"
        )
        self._validate_range(
            speed,
            0,
            MAX_POSITION_SPEED,
            "speed",
            "set_pan_tilt_position"
        )
        if select not in {0, 2}:
            raise InvalidParameter(
                "set_pan_tilt_position",
                "select",
                select,
                valid_range="0 or 2"
            )

        # Format as hex
        pan_hex = self._format_hex(round(pan), 4)
        tilt_hex = self._format_hex(round(tilt), 4)
        speed_hex = self._format_hex(speed, 2)

        cmd = f"APS{pan_hex}{tilt_hex}{speed_hex}{select}"
        url_cmd = self.command_string.format(cmd=cmd)
        response = f"aPS{pan_hex}{tilt_hex}{speed_hex}{select}"
        
        return self._execute_command(
            command_name="set_pan_tilt_position",
            cmd=url_cmd,
            response_pattern=f"^{response}$",
            responses={response: True},
            default=False
        )

    def get_pan_tilt_position(self) -> Optional[Tuple[int, int]]:
        """
        Get current pan and tilt positions.

        Returns:
            Tuple of (pan, tilt) position values, or None if query fails
            
        Raises:
            CommandFailed: If command fails
        """
        url_cmd = self.command_string.format(cmd="APC")
        response = self._execute_query_command(
            command_name="get_pan_tilt_position",
            cmd=url_cmd,
            default=None
        )
        
        if response is None:
            raise CommandFailed("get_pan_tilt_position", self.address)
        
        match = re.match(r"^aPC([0-9A-F]{4})([0-9A-F]{4})$", response)
        if match:
            pan = int(match.group(1), 16)
            tilt = int(match.group(2), 16)
            return (pan, tilt)
        
        return None

    def set_zoom(self, zoom: int) -> bool:
        """
        Set the zoom level.

        Args:
            zoom: Zoom value (1365-4095)

        Returns:
            True if command successful, False otherwise
            
        Raises:
            InvalidParameter: If zoom is invalid
        """
        self._validate_range(
            zoom,
            self.zoom_min,
            self.zoom_max,
            "zoom",
            "set_zoom"
        )

        zoom_hex = self._format_hex(round(zoom), 3)
        cmd = f"AXZ{zoom_hex}"
        url_cmd = self.command_string.format(cmd=cmd)
        response = f"axz{zoom_hex.lower()}"
        
        return self._execute_command(
            command_name="set_zoom",
            cmd=url_cmd,
            response_pattern=f"^{response}$",
            responses={response: True},
            default=False
        )

    def get_zoom(self) -> Optional[int]:
        """
        Get current zoom level.

        Returns:
            Current zoom value, or None if query fails
            
        Raises:
            CommandFailed: If command fails
        """
        url_cmd = self.command_string.format(cmd="GZ")
        response = self._execute_query_command(
            command_name="get_zoom",
            cmd=url_cmd,
            default=None
        )
        
        if response is None:
            raise CommandFailed("get_zoom", self.address)
        
        match = re.match(r"^gz([0-9A-F]{3})$", response)
        if match:
            return int(match.group(1), 16)
        
        return None

    def set_auto_focus(self, enabled: bool) -> bool:
        """
        Enable or disable auto focus.

        Args:
            enabled: True to enable auto focus, False to disable

        Returns:
            True if command successful, False otherwise
            
        Raises:
            InvalidParameter: If enabled is not a boolean
        """
        if not isinstance(enabled, bool):
            raise InvalidParameter(
                "set_auto_focus",
                "enabled",
                enabled,
                valid_range="boolean"
            )

        setting = "1" if enabled else "0"
        cmd = f"D1{setting}"
        url_cmd = self.command_string.format(cmd=cmd)
        
        responses = {
            "d10": not enabled,
            "d11": enabled
        }
        
        return self._execute_command(
            command_name="set_auto_focus",
            cmd=url_cmd,
            response_pattern=r"^d1([0-1])$",
            responses=responses,
            default=False
        )

    def get_auto_focus(self) -> Optional[str]:
        """
        Get current auto focus state.

        Returns:
            'On' if enabled, 'Off' if disabled, or None if query fails
            
        Raises:
            CommandFailed: If command fails
        """
        url_cmd = self.command_string.format(cmd="D1")
        response = self._execute_query_command(
            command_name="get_auto_focus",
            cmd=url_cmd,
            default=None
        )
        
        if response is None:
            raise CommandFailed("get_auto_focus", self.address)
        
        match = re.match(r"^d1([0-1])$", response)
        if match:
            return 'On' if int(match.group(1)) == 1 else 'Off'
        
        return None

    def set_tally(self, enabled: bool) -> bool:
        """
        Enable or disable the tally light.

        Args:
            enabled: True to enable tally light, False to disable

        Returns:
            True if command successful, False otherwise
            
        Raises:
            InvalidParameter: If enabled is not a boolean
        """
        if not isinstance(enabled, bool):
            raise InvalidParameter(
                "set_tally",
                "enabled",
                enabled,
                valid_range="boolean"
            )

        setting = "1" if enabled else "0"
        cmd = f"DA{setting}"
        url_cmd = self.command_string.format(cmd=cmd)
        
        responses = {
            "dA0": not enabled,
            "dA1": enabled
        }
        
        return self._execute_command(
            command_name="set_tally",
            cmd=url_cmd,
            response_pattern=r"^dA([0-1])$",
            responses=responses,
            default=False
        )

    def close(self) -> None:
        """Close the HTTP session and clean up resources."""
        if self.session:
            self.session.close()
            self.logger.debug("HTTP session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the camera."""
        return f"PTZCamera(model={self.camera}, address={self.address})"