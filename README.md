# pynasonic-ptz

A Python library for controlling Panasonic PTZ cameras over their HTTP interface, following
Panasonic's *HD/4K Integrated Camera Interface Specifications*.

## Installation

```bash
pip install git+https://github.com/Chrisrdouglas/pynasonic_ptz.git
```

## Usage

```python
from pynasonic_ptz import PowerState, PTZCamera

cam = PTZCamera("192.168.0.10")  # model defaults to "AW-HN40"

# Power
if cam.get_power_state() is not PowerState.ON:  # ON, STANDBY or TRANSITIONING
    cam.set_power_state(True)                   # False puts it in standby

# Presets are numbered from 0, so preset 0 is "Preset 001" on the camera
cam.move_to_preset(0)
cam.register_preset(12)

# Absolute pan/tilt. Limits depend on the model; 0x8000 is center.
cam.pan_bounds   # (11529, 54005) on the AW-HN40
cam.tilt_bounds  # (21845, 36408) on the AW-HN40
cam.set_pan_tilt_position(0x8000, 0x8000)
cam.set_pan_tilt_position(0x8000, 0x8000, speed=10, fast=False)  # speed is 0-29
pan, tilt = cam.get_pan_tilt_position()

# Continuous pan/tilt: 50 stops an axis, 1-49 moves left/down, 51-99 moves right/up
cam.set_pan_tilt_speed(pan=70, tilt=50)
cam.set_pan_tilt_speed(pan=50, tilt=50)

# Zoom, from 0x555 (wide) to 0xFFF (tele)
cam.ZOOM_BOUNDS  # (1365, 4095)
cam.set_zoom(0x555)
zoom = cam.get_zoom()

# Auto focus and tally
cam.set_auto_focus(True)
cam.get_auto_focus()  # True or False
cam.set_tally(True)
```

Setters return `None`. Every error the library raises is a `PTZError`:

- `CommandFailed` when the camera can't be reached, returns an HTTP error, or rejects the
  command (for example `ER2` while it is in standby).
- `InvalidParameter` (also a `ValueError`) when an argument is outside the range the camera
  accepts. Nothing is sent in that case.
- `InvalidCamera` (also a `ValueError`) when the model isn't in `pynasonic_ptz.CAMERAS`. Pass
  `allow_unknown_model=True` to fall back to the full protocol range instead.

The camera needs a gap between commands (130 ms on the AW-HN40), so `PTZCamera` spaces its
commands out automatically and serializes them if you share one instance across threads.

See `examples/` for complete scripts.

## Supported cameras

### Tested
- AW-HN40

### Untested
Limits for these come from Panasonic's specification, but they haven't been tried on real
hardware.

- HE40 series: AW-HE35, AW-HE38, AW-HE40, AW-HE48, AW-HE58, AW-HE65, AW-HE70, AW-HN38,
  AW-HN65, AW-HN70
- UE70 series: AW-UE63, AW-UE65, AW-UE70, AW-UN70
- HE42 series: AW-HE42, AW-HE68, AW-HE75
- UE150 series: AW-UE150, AW-UE155, AW-UN145
- AW-HE130, AW-HR140

### Not supported
- AW-HE50, AW-HE60, AW-HE120: these don't accept the `#APS` command that
  `set_pan_tilt_position` sends. The other methods should work with `allow_unknown_model=True`.
- AK-UB300: it has no pan-tilt head.

## Development

```bash
pip install -e .[test]
pytest
```

## TODO
- add support for HTTPS
- verify the untested cameras
- add `get_focus` and `set_focus`
