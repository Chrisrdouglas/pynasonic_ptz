"""Work out which preset a camera is sitting on by visiting each one and comparing positions."""
from time import sleep

from pynasonic_ptz import PTZCamera

CAMERA_IP = "192.168.86.218"
PRESETS_TO_CHECK = range(5)


def read_position(cam):
    return (cam.get_zoom(), *cam.get_pan_tilt_position())


def main():
    cam = PTZCamera(CAMERA_IP)

    current = read_position(cam)
    print(f"Current position: {current}")

    presets_by_position = {}
    for preset in PRESETS_TO_CHECK:
        cam.move_to_preset(preset)
        sleep(3)
        position = read_position(cam)
        print(f"Preset {preset + 1}: {position}")
        presets_by_position[position] = preset

    zoom, pan, tilt = current
    cam.set_zoom(zoom)
    cam.set_pan_tilt_position(pan, tilt)

    preset = presets_by_position.get(current)
    if preset is None:
        print("Camera is not on any of the checked presets")
    else:
        # Presets are numbered from 0 here but from 1 on the camera.
        print(f"Camera is on preset {preset + 1}")


if __name__ == "__main__":
    main()
