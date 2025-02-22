from time import sleep

from PTZCamera import PTZCamera

def run():
    camera_ip = '192.168.86.218'
    ptz = PTZCamera(address=camera_ip, debug=True)

    cur_zoom = ptz.getZoom()
    cur_pan, cur_tilt = ptz.getPanTiltPosition()
    print(f'Current Position - {(cur_zoom, cur_pan, cur_tilt)}')

    # create mapping for preset
    preset_mapping = {}
    #for preset_num in range(ptz.presetLower, ptz.presetUpper):
    for preset_num in range(ptz.presetLower, 5):
        ptz.moveToPreset(preset_num)
        sleep(3)
        position = (ptz.getZoom(), *ptz.getPanTiltPosition())
        print(f'position {preset_num + 1} - {position}')
        preset_mapping[position] = preset_num

    ptz.setZoom(cur_zoom)
    ptz.setPanTiltPosition(cur_pan, cur_tilt)

    cur_preset = preset_mapping.get((cur_zoom, cur_pan, cur_tilt), "UNKNOWN")
    print(f"Camera is currently on preset {cur_preset + 1}")  # starts counting at zero

if __name__ == '__main__':
    run()


