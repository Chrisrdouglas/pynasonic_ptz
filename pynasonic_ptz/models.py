"""Per-model limits, taken from the HD/4K Integrated Camera Interface Specifications."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AxisSpec:
    angles: tuple[int, int]
    """Mechanical range in degrees."""
    bounds: tuple[int, int]
    """Inclusive range of raw position values accepted by #APS and returned by #APC."""


@dataclass(frozen=True)
class CameraSpec:
    pan: AxisSpec
    tilt: AxisSpec
    command_delay: float = 0.13
    """Minimum gap between commands, in seconds."""
    max_speed: int | None = None
    """Maximum pan/tilt speed in degrees per second, where known."""


PAN = AxisSpec(angles=(-175, 175), bounds=(0x2D09, 0xD2F5))
TILT_TO_90 = AxisSpec(angles=(-30, 90), bounds=(0x5555, 0x8E38))
TILT_TO_210 = AxisSpec(angles=(-30, 210), bounds=(0x1C71, 0x8E38))

# The AW-HE50, AW-HE60 and AW-HE120 are left out because they lack #APS, which
# set_pan_tilt_position relies on. The AK-UB300 has no pan-tilt head.
CAMERAS: dict[str, CameraSpec] = {
    **dict.fromkeys(
        [
            # HE40 series
            "AW-HE35", "AW-HE38", "AW-HE40", "AW-HE48", "AW-HE58", "AW-HE65", "AW-HE70",
            "AW-HN38", "AW-HN65", "AW-HN70",
            # UE70 series
            "AW-UE63", "AW-UE65", "AW-UE70", "AW-UN70",
            # HE42 series
            "AW-HE42", "AW-HE68", "AW-HE75",
        ],
        CameraSpec(pan=PAN, tilt=TILT_TO_90),
    ),
    **dict.fromkeys(
        ["AW-HE130", "AW-HR140", "AW-UE155", "AW-UN145"],
        CameraSpec(pan=PAN, tilt=TILT_TO_210),
    ),
    "AW-HN40": CameraSpec(pan=PAN, tilt=TILT_TO_90, max_speed=90),
    "AW-UE150": CameraSpec(pan=PAN, tilt=TILT_TO_210, command_delay=0.04, max_speed=180),
}

GENERIC_SPEC = CameraSpec(
    pan=AxisSpec(angles=(-175, 175), bounds=(0x0000, 0xFFFF)),
    tilt=AxisSpec(angles=(-30, 90), bounds=(0x0000, 0xFFFF)),
)
"""Used for models not in CAMERAS: the full protocol range and the spec's default command gap."""
