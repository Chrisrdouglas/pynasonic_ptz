"""Walk a camera through its first presets, its pan/tilt limits and its zoom range."""
from time import sleep

from pynasonic_ptz import PowerState, PTZCamera

CAMERA_IP = "192.168.86.38"
HOME = (0x8000, 0x8000)


def main():
    cam = PTZCamera(CAMERA_IP)

    if cam.get_power_state() is not PowerState.ON:
        cam.set_power_state(True)
        while cam.get_power_state() is not PowerState.ON:
            sleep(1)

    for preset in range(5):
        cam.move_to_preset(preset)
        sleep(4)

    pan_low, pan_high = cam.pan_bounds
    tilt_low, tilt_high = cam.tilt_bounds
    home_pan, home_tilt = HOME
    extremes = [(home_pan, tilt_high), (home_pan, tilt_low), (pan_high, home_tilt), (pan_low, home_tilt)]

    cam.set_pan_tilt_position(*HOME)
    for extreme in extremes:
        for pan, tilt in (extreme, HOME):
            cam.set_pan_tilt_position(pan, tilt)
            sleep(2)
            print(cam.get_pan_tilt_position())

    zoom_low, zoom_high = cam.ZOOM_BOUNDS
    for zoom in (zoom_high, (zoom_low + zoom_high) // 2, zoom_low):
        cam.set_zoom(zoom)
        sleep(2)

    cam.set_power_state(False)


if __name__ == "__main__":
    main()
