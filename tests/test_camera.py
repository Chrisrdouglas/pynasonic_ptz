import pytest
import requests

from pynasonic_ptz import (
    CAMERAS,
    CommandFailed,
    InvalidCamera,
    InvalidParameter,
    PowerState,
    PTZCamera,
    PTZError,
)
from pynasonic_ptz import camera as camera_module


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code


class FakeCamera:
    """Stands in for requests.get, answering commands from a dict of responses."""

    def __init__(self):
        self.responses = {}
        self.requests = []

    def __call__(self, url, params, timeout):
        self.requests.append((url, params, timeout))
        response = self.responses[params["cmd"].removeprefix("#")]
        if isinstance(response, Exception):
            raise response
        if isinstance(response, FakeResponse):
            return response
        return FakeResponse(response)

    @property
    def commands(self):
        return [params["cmd"] for _, params, _ in self.requests]


class FakeClock:
    def __init__(self):
        self.now = 1000.0
        self.sleeps = []

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(camera_module, "time", clock)
    return clock


@pytest.fixture
def fake(monkeypatch, clock):
    fake = FakeCamera()
    monkeypatch.setattr(camera_module.requests, "get", fake)
    return fake


@pytest.fixture
def cam(fake):
    return PTZCamera("192.168.0.10")


def test_request_matches_spec_url_format(cam, fake):
    fake.responses["PTS5050"] = "pTS5050"
    cam.set_pan_tilt_speed(50, 50)

    url, params, timeout = fake.requests[0]
    prepared = requests.Request("GET", url, params=params).prepare()
    assert prepared.url == "http://192.168.0.10/cgi-bin/aw_ptz?cmd=%23PTS5050&res=1"
    assert timeout == cam.timeout


@pytest.mark.parametrize(
    "response, state",
    [("p0", PowerState.STANDBY), ("p1", PowerState.ON), ("p3", PowerState.TRANSITIONING)],
)
def test_get_power_state(cam, fake, response, state):
    fake.responses["O"] = response
    assert cam.get_power_state() is state


@pytest.mark.parametrize("on, command, response", [(True, "O1", "p1"), (False, "O0", "p0")])
def test_set_power_state(cam, fake, on, command, response):
    fake.responses[command] = response
    cam.set_power_state(on)
    assert fake.commands == [f"#{command}"]


def test_set_pan_tilt_speed_pads_to_two_digits(cam, fake):
    fake.responses["PTS0199"] = "pTS0199"
    cam.set_pan_tilt_speed(1, 99)
    assert fake.commands == ["#PTS0199"]


@pytest.mark.parametrize("pan, tilt", [(0, 50), (100, 50), (50, 0), (50, -1), (50, 5.0)])
def test_set_pan_tilt_speed_rejects_out_of_range(cam, fake, pan, tilt):
    with pytest.raises(InvalidParameter):
        cam.set_pan_tilt_speed(pan, tilt)
    assert fake.requests == []


def test_set_pan_tilt_position_formats_hex(cam, fake):
    fake.responses["APS800080001D2"] = "aPS800080001D2"
    cam.set_pan_tilt_position(0x8000, 0x8000)
    assert fake.commands == ["#APS800080001D2"]


def test_set_pan_tilt_position_slow_table_and_rounding(cam, fake):
    fake.responses["APS2D0955550A0"] = "aPS2D0955550A0"
    cam.set_pan_tilt_position(0x2D09 + 0.4, 0x5555, speed=10, fast=False)
    assert fake.commands == ["#APS2D0955550A0"]


def test_set_pan_tilt_position_accepts_inclusive_bounds(cam, fake):
    fake.responses["APSD2F58E381D2"] = "aPSD2F58E381D2"
    cam.set_pan_tilt_position(0xD2F5, 0x8E38)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pan": 0x2D08, "tilt": 0x8000},
        {"pan": 0xD2F6, "tilt": 0x8000},
        {"pan": 0x8000, "tilt": 0x5554},
        {"pan": 0x8000, "tilt": 0x8E39},
        {"pan": 0x8000, "tilt": 0x8000, "speed": 30},
        {"pan": 0x8000, "tilt": 0x8000, "speed": -1},
    ],
)
def test_set_pan_tilt_position_rejects_out_of_range(cam, fake, kwargs):
    with pytest.raises(InvalidParameter):
        cam.set_pan_tilt_position(**kwargs)
    assert fake.requests == []


def test_get_pan_tilt_position(cam, fake):
    fake.responses["APC"] = "aPC80008E38"
    assert cam.get_pan_tilt_position() == (0x8000, 0x8E38)


@pytest.mark.parametrize("method, command", [("move_to_preset", "R"), ("register_preset", "M")])
def test_presets_are_zero_padded(cam, fake, method, command):
    fake.responses[f"{command}07"] = "s07"
    getattr(cam, method)(7)
    assert fake.commands == [f"#{command}07"]


@pytest.mark.parametrize("preset", [-1, 100, 3.0, "3"])
def test_presets_reject_invalid(cam, fake, preset):
    with pytest.raises(InvalidParameter):
        cam.move_to_preset(preset)


def test_set_zoom(cam, fake):
    fake.responses["AXZFFF"] = "axzFFF"
    cam.set_zoom(0xFFF)
    assert fake.commands == ["#AXZFFF"]


@pytest.mark.parametrize("zoom", [0x554, 0x1000])
def test_set_zoom_rejects_out_of_range(cam, fake, zoom):
    with pytest.raises(InvalidParameter):
        cam.set_zoom(zoom)


def test_get_zoom(cam, fake):
    fake.responses["GZ"] = "gz555"
    assert cam.get_zoom() == 1365


@pytest.mark.parametrize("response, enabled", [("d10", False), ("d11", True)])
def test_get_auto_focus(cam, fake, response, enabled):
    fake.responses["D1"] = response
    assert cam.get_auto_focus() is enabled


@pytest.mark.parametrize("method, command, response", [
    ("set_auto_focus", "D1", "d1"),
    ("set_tally", "DA", "dA"),
])
def test_boolean_setters(cam, fake, method, command, response):
    fake.responses[f"{command}1"] = f"{response}1"
    fake.responses[f"{command}0"] = f"{response}0"
    getattr(cam, method)(True)
    getattr(cam, method)(False)
    assert fake.commands == [f"#{command}1", f"#{command}0"]


def test_error_response_raises(cam, fake):
    fake.responses["R05"] = "ER2:R05"
    with pytest.raises(CommandFailed, match="busy or in standby") as info:
        cam.move_to_preset(5)
    assert info.value.command == "R05"
    assert info.value.address == "192.168.0.10"


def test_unexpected_control_response_raises(cam, fake):
    fake.responses["D11"] = "d10"
    with pytest.raises(CommandFailed, match="expected 'd11', got 'd10'"):
        cam.set_auto_focus(True)


def test_unexpected_query_response_raises(cam, fake):
    fake.responses["GZ"] = "garbage"
    with pytest.raises(CommandFailed, match="unexpected response"):
        cam.get_zoom()


def test_http_error_raises(cam, fake):
    fake.responses["GZ"] = FakeResponse("", status_code=403)
    with pytest.raises(CommandFailed, match="HTTP 403"):
        cam.get_zoom()


def test_network_error_is_wrapped(cam, fake):
    fake.responses["GZ"] = requests.ConnectionError("unreachable")
    with pytest.raises(CommandFailed) as info:
        cam.get_zoom()
    assert isinstance(info.value.__cause__, requests.ConnectionError)


def test_errors_are_ordinary_exceptions():
    assert issubclass(PTZError, Exception)
    assert issubclass(InvalidParameter, ValueError)


def test_unknown_model_raises():
    with pytest.raises(InvalidCamera):
        PTZCamera(model="AW-XX999")


def test_unknown_model_allowed_uses_full_range(fake):
    with pytest.warns(UserWarning):
        cam = PTZCamera(model="AW-XX999", allow_unknown_model=True)
    assert cam.pan_bounds == (0, 0xFFFF)
    assert cam.tilt_bounds == (0, 0xFFFF)


def test_commands_are_spaced_by_model_delay(cam, fake, clock):
    fake.responses["GZ"] = "gz555"
    cam.get_zoom()
    clock.now += 0.05
    cam.get_zoom()
    clock.now += 1
    cam.get_zoom()
    assert clock.sleeps == [pytest.approx(0.08)]


@pytest.mark.parametrize(
    "model, tilt_angles, tilt_bounds",
    [
        ("AW-HN40", (-30, 90), (0x5555, 0x8E38)),
        ("AW-UE70", (-30, 90), (0x5555, 0x8E38)),
        ("AW-HE42", (-30, 90), (0x5555, 0x8E38)),
        ("AW-UE150", (-30, 210), (0x1C71, 0x8E38)),
        ("AW-HE130", (-30, 210), (0x1C71, 0x8E38)),
    ],
)
def test_model_limits_match_spec(model, tilt_angles, tilt_bounds):
    spec = CAMERAS[model]
    assert spec.pan.angles == (-175, 175)
    assert spec.pan.bounds == (0x2D09, 0xD2F5)
    assert spec.tilt.angles == tilt_angles
    assert spec.tilt.bounds == tilt_bounds


@pytest.mark.parametrize("model", ["AW-HE50", "AW-HE60", "AW-HE120", "AK-UB300"])
def test_models_without_aps_are_not_listed(model):
    assert model not in CAMERAS
