# Pynasonic PTZ

A Python library for controlling Panasonic PTZ cameras via HTTP API with robust error handling, type safety, and logging.

Supports Panasonic camera models including AW-HN40, AW-UE150, and others with similar HTTP API interfaces.

## Installation

### From GitHub
```bash
pip install git+https://github.com/Chrisrdouglas/pynasonic_ptz.git
```

### From Source
```bash
git clone https://github.com/Chrisrdouglas/pynasonic_ptz.git
cd pynasonic_ptz
pip install .
```

### Development Installation
```bash
git clone https://github.com/Chrisrdouglas/pynasonic_ptz.git
cd pynasonic_ptz
pip install -e ".[dev]"
```

## Quick Start

```python
from pynasonic_ptz import PTZCamera
import logging

# Enable debug logging (optional)
logging.basicConfig(level=logging.DEBUG)

# Create camera instance
with PTZCamera(address="192.168.0.10") as camera:
    # Power on
    camera.set_power_state(True)
    
    # Move to preset
    camera.move_to_preset(5)
    
    # Get current position
    pan, tilt = camera.get_pan_tilt_position()
    print(f"Position: pan={pan}, tilt={tilt}")
    
    # Set zoom
    camera.set_zoom(2500)
    
    # Enable auto focus
    camera.set_auto_focus(True)
```

## Basic Usage

### Initialize Camera

```python
from pynasonic_ptz import PTZCamera

# Basic initialization
camera = PTZCamera(address="192.168.0.10")

# With all options
camera = PTZCamera(
    camera="AW-UE150",           # Camera model
    address="192.168.0.10",      # IP address
    protocol="http",              # http or https
    timeout=10.0,                 # Request timeout in seconds
    retry_attempts=3,             # Number of retries
    use_default_on_unknown=False  # Use default config for unknown models
)

# Don't forget to clean up
camera.close()

# Or use context manager (recommended)
with PTZCamera(address="192.168.0.10") as camera:
    # Your code here
    pass  # Automatic cleanup
```

### Power Control

```python
# Check power state
state = camera.get_power_state()  # Returns: "On", "Standby", "Transitioning", or "Off"

# Power on
camera.set_power_state(True)

# Power off
camera.set_power_state(False)
```

### Presets

```python
# Move to preset
camera.move_to_preset(5)

# Get preset bounds
min_preset, max_preset = camera.preset_bounds  # e.g., (0, 99)
```

### Pan/Tilt Control

```python
# Get current position
pan, tilt = camera.get_pan_tilt_position()

# Move to absolute position
camera.set_pan_tilt_position(
    pan=32768,
    tilt=28000,
    speed=20,   # Speed (0-29)
    select=0    # 0=slow, 2=fast
)

# Set pan/tilt speed
camera.set_pan_tilt_speed(pan_speed=50, tilt_speed=50)

# Get position bounds
pan_min, pan_max = camera.pan_bounds
tilt_min, tilt_max = camera.tilt_bounds
```

### Zoom Control

```python
# Get current zoom
zoom = camera.get_zoom()

# Set zoom
camera.set_zoom(2500)

# Get zoom bounds
zoom_min, zoom_max = camera.zoom_bounds  # e.g., (1365, 4095)
```

### Focus Control

```python
# Enable auto focus
camera.set_auto_focus(True)

# Disable auto focus
camera.set_auto_focus(False)

# Check auto focus state
state = camera.get_auto_focus()  # Returns: "On" or "Off"
```

### Tally Light

```python
# Enable tally light
camera.set_tally(True)

# Disable tally light
camera.set_tally(False)
```

## Error Handling

```python
from pynasonic_ptz import PTZCamera
from pynasonic_ptz import (
    InvalidParameter, 
    CommandFailed, 
    NetworkError, 
    TimeoutError
)

try:
    with PTZCamera("192.168.0.10", timeout=5.0) as camera:
        camera.set_zoom(5000)  # Out of range!
        
except InvalidParameter as e:
    print(f"Invalid parameter: {e}")
    print(f"  Command: {e.command}")
    print(f"  Parameter: {e.param_name}")
    print(f"  Value: {e.value}")
    print(f"  Valid range: {e.valid_range}")
    
except TimeoutError as e:
    print(f"Command timed out: {e}")
    print(f"  Timeout: {e.timeout}s")
    
except NetworkError as e:
    print(f"Network error: {e}")
    print("Check camera connection and power.")
    
except CommandFailed as e:
    print(f"Command failed: {e}")
    if e.status_code:
        print(f"  HTTP Status: {e.status_code}")
```

## Supported Camera Models

- **AW-HN40** - Tested and supported
- **AW-UE150** - Tested and supported
- **Default** - Generic profile for untested models

To see available models:
```python
from pynasonic_ptz import get_available_models
print(get_available_models())  # ['AW-HN40', 'AW-UE150']
```

## Advanced Configuration

### Custom Logger

```python
import logging
from pynasonic_ptz import PTZCamera

# Create custom logger
logger = logging.getLogger("my_camera")
logger.setLevel(logging.DEBUG)

# Use custom logger
camera = PTZCamera(
    address="192.168.0.10",
    logger=logger
)
```

### Unknown Camera Models

```python
# Will raise InvalidCamera exception
camera = PTZCamera(camera="UNKNOWN-MODEL", address="192.168.0.10")

# Use default configuration instead
camera = PTZCamera(
    camera="UNKNOWN-MODEL",
    address="192.168.0.10",
    use_default_on_unknown=True  # Falls back to default config
)
```

### Camera Properties

```python
camera = PTZCamera(address="192.168.0.10")

# Position bounds
print(camera.pan_bounds)        # (11529, 54004)
print(camera.tilt_bounds)       # (21845, 36407)
print(camera.zoom_bounds)       # (1365, 4095)

# Angle ranges (in degrees)
print(camera.pan_angle_range)   # (-30, 210)
print(camera.tilt_angle_range)  # (-30, 90)

# Speed bounds
print(camera.pan_speed_bounds)  # (1, 99)
print(camera.tilt_speed_bounds) # (1, 99)

# Other properties
print(camera.delay)             # 0.13 (command delay in seconds)
print(camera.power_states)      # ('On', 'Standby', 'Transitioning', 'Off')
```

## Examples

The `examples/` directory contains complete working examples:

- **`example_usage.py`** - Demonstrates all major features
- **`preset_mapper.py`** - Maps presets to their positions
- **`test.py`** - Quick test to run before merging code

### Quick Migration Example

```python
# OLD
from PTZCamera import PTZCamera
camera = PTZCamera(address="192.168.0.10", debug=True)
camera.getPowerState()
camera.moveToPreset(5)
camera.setPanTiltPosition(32768, 32768)

# NEW (v0.0.1)
from pynasonic_ptz import PTZCamera
import logging
logging.basicConfig(level=logging.DEBUG)  # Instead of debug=True

with PTZCamera(address="192.168.0.10") as camera:
    camera.get_power_state()
    camera.move_to_preset(5)
    camera.set_pan_tilt_position(32768, 32768, speed=20, select=0)
```

## API Reference

### Camera Control Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get_power_state()` | Get current power state | `str` |
| `set_power_state(power_on)` | Set power state | `str` |
| `move_to_preset(preset_index)` | Move to preset position | `bool` |
| `set_pan_tilt_position(pan, tilt, speed, select)` | Move to absolute position | `bool` |
| `get_pan_tilt_position()` | Get current position | `Tuple[int, int]` |
| `set_pan_tilt_speed(pan_speed, tilt_speed)` | Set movement speeds | `bool` |
| `set_zoom(zoom)` | Set zoom level | `bool` |
| `get_zoom()` | Get current zoom | `int` |
| `set_auto_focus(enabled)` | Enable/disable auto focus | `bool` |
| `get_auto_focus()` | Get auto focus state | `str` |
| `set_tally(enabled)` | Enable/disable tally light | `bool` |
| `close()` | Clean up resources | `None` |

### Exception Classes

| Exception | Description |
|-----------|-------------|
| `PTZCameraError` | Base exception for all camera errors |
| `CommandFailed` | Command failed to execute |
| `InvalidParameter` | Invalid parameter value |
| `InvalidCamera` | Unknown camera model |
| `NetworkError` | Network communication error |
| `TimeoutError` | Request timeout |

### Configuration Functions

| Function | Description | Returns |
|----------|-------------|---------|
| `get_available_models()` | List supported camera models | `list[str]` |
| `get_camera_config(model)` | Get config for camera model | `CameraConfig` |

## Requirements

- Python >= 3.8
- requests >= 2.31.0
- urllib3 >= 2.0.0

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run code quality checks
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/Chrisrdouglas/pynasonic_ptz/issues)
- **Migration Guide**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## Changelog

### v2.0.1 (2026-01-23)

**Major Rewrite**
- Complete refactor with modern Python practices
- Added type hints throughout
- Implemented retry logic and timeouts
- Context manager support
- Better error handling with detailed exceptions
- Consistent snake_case naming
- Improved documentation

**Breaking Changes**
- All method names changed to snake_case
- `setPanTiltPosition` now requires `speed` and `select` parameters
- Import path changed to `pynasonic_ptz`
- `debug` parameter replaced with Python logging

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for full migration instructions.