"""Control of Panasonic PTZ cameras through the aw_ptz HTTP interface.

Command formats follow section 3.1 of the HD/4K Integrated Camera Interface
Specifications.
"""
from __future__ import annotations

import math
import re
import threading
import time
import warnings
from enum import Enum

import requests

from .exceptions import CommandFailed, InvalidCamera, InvalidParameter
from .models import CAMERAS, GENERIC_SPEC

_ERROR_RESPONSES = {
    "ER1": "command not supported by this camera",
    "ER2": "camera is busy or in standby",
    "ER3": "value out of range",
}


class PowerState(Enum):
    STANDBY = "0"
    ON = "1"
    TRANSITIONING = "3"  # standby to on


class PTZCamera:
    """A Panasonic PTZ camera reachable over HTTP.

    Commands are serialized and spaced at least ``spec.command_delay`` apart,
    as the camera requires. Setters return None and raise CommandFailed if the
    camera does not acknowledge the command.
    """

    ZOOM_BOUNDS = (0x555, 0xFFF)
    PRESET_BOUNDS = (0, 99)
    SPEED_BOUNDS = (1, 99)
    POSITION_SPEED_BOUNDS = (0x00, 0x1D)

    def __init__(
        self,
        address: str = "192.168.0.10",
        model: str = "AW-HN40",
        *,
        protocol: str = "http",
        timeout: float = 5.0,
        allow_unknown_model: bool = False,
    ):
        try:
            self.spec = CAMERAS[model]
        except KeyError:
            if not allow_unknown_model:
                raise InvalidCamera(model) from None
            warnings.warn(f"{model} is not a known camera model; using generic limits", stacklevel=2)
            self.spec = GENERIC_SPEC

        self.address = address
        self.model = model
        self.timeout = timeout
        self._url = f"{protocol}://{address}/cgi-bin/aw_ptz"
        self._lock = threading.Lock()
        self._last_sent = -math.inf

    def __repr__(self) -> str:
        return f"{type(self).__name__}(address={self.address!r}, model={self.model!r})"

    @property
    def pan_bounds(self) -> tuple[int, int]:
        return self.spec.pan.bounds

    @property
    def tilt_bounds(self) -> tuple[int, int]:
        return self.spec.tilt.bounds

    def get_power_state(self) -> PowerState:
        return PowerState(self._query("O", r"p([013])")[1])

    def set_power_state(self, on: bool) -> None:
        """Turn the camera on, or put it in standby."""
        value = "1" if on else "0"
        self._control(f"O{value}", f"p{value}")

    def set_pan_tilt_speed(self, pan: int, tilt: int) -> None:
        """Start moving continuously, or stop.

        Each speed is 1-99: 50 stops that axis, 1-49 moves left/down and 51-99
        moves right/up, faster the farther the value is from 50.
        """
        _check_range("pan", pan, self.SPEED_BOUNDS)
        _check_range("tilt", tilt, self.SPEED_BOUNDS)
        data = f"{pan:02d}{tilt:02d}"
        self._control(f"PTS{data}", f"pTS{data}")

    def set_pan_tilt_position(self, pan: float, tilt: float, speed: int = 0x1D, *, fast: bool = True) -> None:
        """Move to an absolute position.

        pan and tilt must fall within pan_bounds and tilt_bounds; 0x8000 is
        center for both. speed is 0-29 (29 is fastest), and fast selects the
        camera's fast speed table rather than its slow one.
        """
        pan, tilt = round(pan), round(tilt)
        _check_range("pan", pan, self.pan_bounds)
        _check_range("tilt", tilt, self.tilt_bounds)
        _check_range("speed", speed, self.POSITION_SPEED_BOUNDS)
        data = f"{pan:04X}{tilt:04X}{speed:02X}{2 if fast else 0}"
        self._control(f"APS{data}", f"aPS{data}")

    def get_pan_tilt_position(self) -> tuple[int, int]:
        match = self._query("APC", r"aPC([0-9A-F]{4})([0-9A-F]{4})")
        return int(match[1], 16), int(match[2], 16)

    def move_to_preset(self, preset: int) -> None:
        """Recall a preset. Presets are numbered from 0, so 0 is "Preset 001" on the camera."""
        _check_range("preset", preset, self.PRESET_BOUNDS)
        self._control(f"R{preset:02d}", f"s{preset:02d}")

    def register_preset(self, preset: int) -> None:
        """Save the current position as a preset. Presets are numbered from 0."""
        _check_range("preset", preset, self.PRESET_BOUNDS)
        self._control(f"M{preset:02d}", f"s{preset:02d}")

    def set_zoom(self, zoom: int) -> None:
        """Zoom to a position within ZOOM_BOUNDS: 0x555 is wide, 0xFFF is tele."""
        _check_range("zoom", zoom, self.ZOOM_BOUNDS)
        self._control(f"AXZ{zoom:03X}", f"axz{zoom:03X}")

    def get_zoom(self) -> int:
        return int(self._query("GZ", r"gz([0-9A-F]{3})")[1], 16)

    def get_auto_focus(self) -> bool:
        return self._query("D1", r"d1([01])")[1] == "1"

    def set_auto_focus(self, enabled: bool) -> None:
        value = "1" if enabled else "0"
        self._control(f"D1{value}", f"d1{value}")

    def set_tally(self, on: bool) -> None:
        """Turn the red tally lamp on or off."""
        value = "1" if on else "0"
        self._control(f"DA{value}", f"dA{value}")

    def _control(self, command: str, expected: str) -> None:
        response = self._send(command)
        if response != expected:
            raise CommandFailed(command, self.address, f"expected {expected!r}, got {response!r}")

    def _query(self, command: str, pattern: str) -> re.Match[str]:
        response = self._send(command)
        match = re.fullmatch(pattern, response)
        if match is None:
            raise CommandFailed(command, self.address, f"unexpected response {response!r}")
        return match

    def _send(self, command: str) -> str:
        with self._lock:
            wait = self._last_sent + self.spec.command_delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            try:
                response = requests.get(
                    self._url,
                    params={"cmd": f"#{command}", "res": 1},
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                raise CommandFailed(command, self.address, str(exc)) from exc
            finally:
                self._last_sent = time.monotonic()

        if response.status_code != 200:
            raise CommandFailed(command, self.address, f"HTTP {response.status_code}")
        body = response.text.strip()
        error = _ERROR_RESPONSES.get(body.partition(":")[0])
        if error:
            raise CommandFailed(command, self.address, f"{error} ({body})")
        return body


def _check_range(name: str, value: int, bounds: tuple[int, int]) -> None:
    low, high = bounds
    if not (isinstance(value, int) and low <= value <= high):
        raise InvalidParameter(name, value, bounds)
