from time import sleep
import PTZCamera
cam = PTZCamera.PTZCamera(address="192.168.86.38")
if cam.getPowerState() != "On":
    cam.setPowerState(True)
    while cam.getPowerState() == "Transitioning":
        continue
sleep(4)
cam.moveToPreset(0)
sleep(4)
cam.moveToPreset(1)
sleep(4)
cam.moveToPreset(2)
sleep(4)
cam.moveToPreset(3)
sleep(4)
cam.moveToPreset(4)

cam.setPanTiltPosition(32767.5,32767.5)
sleep(2)
cam.setPanTiltPosition(32767.5,65535)
sleep(2)
cam.setPanTiltPosition(32767.5,32767.5)
sleep(2)
cam.setPanTiltPosition(32767.5,0)
sleep(2)
cam.setPanTiltPosition(32767.5,32767.5)
sleep(2)
cam.setPanTiltPosition(65535,32767.5)
sleep(2)
cam.setPanTiltPosition(32767.5,32767.5)
sleep(2)
cam.setPanTiltPosition(0,32767.5)
sleep(2)
cam.setPanTiltPosition(32767.5,32767.5)
sleep(2)



cam.setZoom(4095)
sleep(2)
cam.setZoom(2730)
sleep(2)
cam.setZoom(1365)
sleep(2)

cam.setPowerState(False)