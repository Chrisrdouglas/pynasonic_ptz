class PTZError(Exception):
    """Base class for every error raised by pynasonic_ptz."""


class CommandFailed(PTZError):
    """The camera could not be reached or did not accept a command."""

    def __init__(self, command: str, address: str, reason: str):
        self.command = command
        self.address = address
        self.reason = reason
        super().__init__(f"#{command} failed on {address}: {reason}")


class InvalidParameter(PTZError, ValueError):
    """An argument is outside the range the camera accepts."""

    def __init__(self, name: str, value, bounds: tuple[int, int]):
        self.name = name
        self.value = value
        self.bounds = bounds
        low, high = bounds
        super().__init__(f"{name} must be an int from {low} to {high}, got {value!r}")


class InvalidCamera(PTZError, ValueError):
    """The camera model has no entry in pynasonic_ptz.CAMERAS."""

    def __init__(self, model: str):
        self.model = model
        super().__init__(
            f"{model!r} is not a known camera model. Known models are listed in "
            "pynasonic_ptz.CAMERAS; pass allow_unknown_model=True to use generic limits."
        )
