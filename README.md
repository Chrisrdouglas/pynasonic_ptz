# pynasonicPTZ

A python library for interfacing with the Panasonic family of cameras over HTTP.

# How to use
```python
import PTZCamera
cam = PTZCamera(address='192.168.0.10')

# check if camera is on or not
cam.getPowerState()
# returns ("On", "Off", "Transitioning")

cam.panBounds()
# returns (0, 65535)

cam.tiltBounds()
# returns (0, 65535)

cam.zoomBounds()
# returns (1365, 4095)

# Turn Camera On
state = True
cam.setPowerState(cameraPowerState=state)

# Turn Camera Off
state = False
cam.setPowerState(cameraPowerState=state)

# Move To Preset Position (defaults to position 0)
preset = 12
cam.moveToPreset(preset_index=12)

# Register New Preset
preset = 12
cam.registerPreset(preset_index=12)

# Move Camera To New Position
# the pan and tilt values must be between an int 0 and 65535
# to move it to the middle of both you would use floor(65535/2)
pan = int(65535/2)
tilt = int(65535/2)
cam.setPanTiltPosition(pan=pan, tilt=tilt)

pan = 0
tilt = 0
cam.setPanTiltPosition(pan=pan, tilt=tilt)

pan = 65535
tilt = 65535
cam.setPanTiltPosition(pan=pan, tilt=tilt)


# Get Pan and Tilt Position
pan, tilt = cam.getPanTiltPosition()


# Set Zoom
# to zoom all the way out
zoom = 1365
cam.setZoom(zoom=zoom)

# to zoom all the way in
zoom = 4095
cam.setZoom(zoom=zoom)

# Get Zoom
zoom = cam.getZoom()
# returns a number between 1365 and 4095

# Get Auto Focus
cam.getAutoFocus()
# returns "On" or "Off

# Set Auto Focus
# Turn on with True, off with False
cam.setAutoFocus(value=True)
# or
cam.setAutoFocus(value=False)
# both return True if it worked, false otherwise

```

# Supported Cameras
## Tested
- AW-HN40

## Untested
- AW-HE120
- AW-HE60
- AW-HE130
- AW-HE40
- AW-UE70
- AW-HE40
- AK-UB300
- AW-HR140
- AW-UE150
- AW-UE150 (v2.1)
- AK-UB400 (v7.4)
- AW-UE150 (v2.28)
- AW-HE42 (v2.28)
- AW-UN145


# TODO
- add support for HTTPS
- enhance _execute_command() to have better support for multithreading
- verify the untested cameras
- make getFocus and setFocus