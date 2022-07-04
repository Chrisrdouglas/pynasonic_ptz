DEFAULT_CAMERA = "AW-HN40"
DEFUALT_IP = "192.168.0.10"
DEFAULT_PROTOCOL = "http"

#Unsupported functions
UNSUPPORTED_CAMERA_FUNCTIONS = {
    "AK-UB300": {"getCameraPower", "setCameraPower", "moveToPreset"}
}

# cameras
CAMERAS = {
    "AW-HN40": {
        "commandString": "{protocol}://{address}/cgi-bin/aw_ptz?cmd=%23{cmd}&res=1",
        "commands": {
            "getPowerState": {
                "cmd": "O",
                "responsePattern":"^p(\\d)$",
                "dynamicResponse": False,
                "response": {
                    "default": "Off",
                    'p0': "Standby",
                    'p1': "On",
                    'p3': "Transitioning"}
                },
            "setPowerState": {
                "cmd": "O{value}",
                "responsePattern":"^p(\\d)$",
                "dynamicResponse": False,
                "response": {
                    "default": "Off",
                    'p0': "Standby",
                    'p1': "On"}
                },
            "moveToPreset": {
                "cmd": "R{value}",
                "responsePattern":"^s{value}$",
                "dynamicResponse": True,
                },
            "registerPreset": {
                "cmd": "M{value}"
                }
        },
    }

}