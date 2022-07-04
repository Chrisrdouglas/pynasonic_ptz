from time import sleep
import PTZCamera
cam = PTZCamera.PTZCamera(address="192.168.86.38")
if cam.getPowerState() != "On":
    cam.setPowerState(1)
    while cam.getPowerState() == "Transitioning":
        continue

cam.moveToPreset(0)
sleep(4)
cam.moveToPreset(1)
sleep(4)
cam.moveToPreset(2)
sleep(4)
cam.moveToPreset(3)
sleep(4)
cam.moveToPreset(4)




cam.setPowerState(0)
