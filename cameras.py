CAMERAS = {
    "AW-HN40": {
        "pan": {
            "angles": (-30, 210),
            "bounds": (11529, 54005),
            "max_speed": 90, # degrees/second
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 90),
            "bounds": (21845, 36408),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "delay": 0.13
    },
    "AW-UE150": {
        "pan": {
            "angles": (-175, 175),
            "bounds": (11529, 54005),
            "max_speed": 180,
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 210),
            "bounds": (7281, 36408),
            "max_speed": 180,
            "speed_bounds": (1, 100)
        },
        "delay": 0.04
    },
    "default": {
        "pan": {
            "angles": (-175, 175),
            "bounds": (0, 65535),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "tilt": {
            "angles": (-30, 90),
            "bounds": (0, 65535),
            "max_speed": 90,
            "speed_bounds": (1, 100)
        },
        "delay": 0.13
    }
}
