DEFAULT_CAMERA = "AW-HN40"
DEFUALT_IP = "192.168.0.10"
DEFAULT_PROTOCOL = "http"

#Unsupported functions
UNSUPPORTED_CAMERA_FUNCTIONS = {
    "AK-UB300": {"getCameraPower", "setCameraPower", "moveToPreset", "registerPreset"}
}
SUPPORTED_CAMERAS = {
    "AW-HN40": {
        "supported_functions": {
            "panTiltPosition":{
                "pan": {
                    "min": 0,
                    "max": 65535
                    },
                "tilt": {
                    "min": 21845,
                    "max": 36408
                    }
            }
        }
    },
    "AW-HE120": {
        "supported_functions": {
            "panTiltPosition":{
                "pan": {
                    "min": 0,
                    "max": 65535
                    },
                "tilt": {
                    "min": 7281,
                    "max": 36408
                    }
            }
        }
    }
}