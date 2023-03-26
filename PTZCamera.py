from requests import get
import re

from .PTZCameraExceptions import CommandFailed, InvalidParameter, InvalidCamera
from .cameras import CAMERAS

class PTZCamera:
    def __init__(self, camera="AW-HN40", address="192.168.0.10", protocol="http", debug=False):
        '''
            camera: name of the camera model
            address: IP or hostname of the camera
            protocol: either 'http' or 'https' 
        '''
        self.camera = camera
        self.address = address
        self.command_string = "{protocol}://{address}/cgi-bin/aw_ptz?cmd=%23{cmd}&res=1".format(protocol=protocol, address=self.address, cmd="{cmd}")
        self.debug = debug

        try:
            cam_config = CAMERAS[self.camera]
        except KeyError:
            cam_config = CAMERAS["default"]
            if debug:
                print("WARNING: CAMERA NOT FOUND IN cameras.py.")
            else:
                raise InvalidCamera(self.camera)

        # Zoom bounds
        self.zoomUpper = 4096
        self.zoomLower = 1365

        # Tilt bounds
        tilt = cam_config['tilt']['angles']
        self.tiltAngleUpper = tilt[1]
        self.tiltAngleLower = tilt[0]
        tilt = cam_config['tilt']['bounds']
        self.tiltUpper = tilt[1]
        self.tiltLower = tilt[0]

        # Preset bounds
        self.presetUpper = 100
        self.presetLower = 0

        # Pan bounds
        pan = cam_config['pan']['angles']
        self.panAngleUpper = pan[1]
        self.panAngleLower = pan[0]
        pan = cam_config['pan']['bounds']
        self.panUpper = pan[1]
        self.panLower = pan[0]

        self._delay = cam_config['delay']

    @property
    def tiltAngleRange(self):
        return (self.tiltAngleLower, self.tiltAngleUpper)

    @property
    def panAngleRange(self):
        return (self.panAngleLower, self.panAngleUpper)

    @property
    def delay(self):
        return self._delay

    @property
    def powerStates(self):
        return ('On', 'Standby', 'Transitioning')

    @property
    def presetBounds(self):
        return (self.presetLower, self.presetUpper - 1)

    @property
    def panBounds(self):
        return (self.panLower, self.panUpper - 1)

    @property
    def tiltBounds(self):
        return (self.tiltLower, self.tiltUpper - 1)

    @property
    def zoomBounds(self):
        return (self.zoomLower, self.zoomUpper - 1)

    def _zeroPad(self, value, desired_length):
        pad_length = desired_length - len(value)
        return "0"*pad_length + value

    def _zeroPadPreset(self, value):
        if value < 10:
            return "0{0}".format(value)
        return str(value)
    
    def _executeCommand(self, fnName, cmd, responses, response_pattern, default):
        response = default
        r = get(cmd)
        if r.status_code == 200:
            match = re.match(response_pattern, r.text)
            if match is None:
                raise CommandFailed(fnName, self.address)
            response = responses.get(r.text, default)
        else:
            raise CommandFailed(fnName, self.address)
        return response
    
    def _executeQueryCommand(self, fnName, cmd, default):
        response = default
        r = get(cmd)
        if r.status_code == 200:
            response = r.text
        else:
            raise CommandFailed(fnName, self.address)
        return response

    def getPowerState(self):
        '''
        Reads the power state of the camera

            Returns:
                    A string saying what state the camera is in
        '''
        fnName = "getPowerState"
        response_pattern = "^p(\\d)$"
        url_cmd = self.command_string.format(cmd="O")
        default = "Off"
        responses = {
                    'p0': "Standby",
                    'p1': "On",
                    'p3': "Transitioning"
                    }
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)

    def setPowerState(self, cameraPowerState):
        '''
        Changes the Power State of the camera

            Parameters:
                    cameraPowerState (bool): Desired power state for camera. True for on. False for standby
            Returns:
                    A string saying what power state it will be in. On or Standby
        '''
        fnName = "setPowerState"
        responses = {
            'p0': "Standby",
            'p1': "On",
            'p2': "Transferring"
            }
        default = "Off"
        response_pattern = "^p(\\d)$"
        cameraPowerState = "1" if cameraPowerState else "0"
        cmd = "O{value}".format(value=cameraPowerState)
        url_cmd = self.command_string.format(cmd=cmd)
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)
     
    def moveToPreset(self, preset_index):
        '''
        Moves camera to a registered preset position

            Parameters:
                    preset_index (int): ID of the preset registered on the camera
            Returns:
                    True if moving to the preset position. otherwise false
            Raises:
                    InvalidParameter
        '''
        fnName = "moveToPreset"
        if type(preset_index) is not int or preset_index not in range(self.presetLower, self.presetUpper):
            raise InvalidParameter(fnName, 'preset_index', preset_index)
        preset_index = self._zeroPadPreset(preset_index)
        cmd = "R{value}".format(value=preset_index)
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^s{value}$".format(value=preset_index)
        responses = {
            "s{value}".format(value=preset_index): True
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                cmd=url_cmd, 
                                responses=responses,
                                response_pattern=response_pattern,
                                default=default)

    def registerPreset(self, preset_index):
        '''
        Registers the current position as a preset position for a camera

            Parameters:
                    preset_index (int): ID of the preset registered on the camera
            Returns:
                    True if the position has been registered. otherwise false
            Raises:
                    InvalidParameter
        '''
        fnName = "registerPreset"
        if type(preset_index) is not int or preset_index not in range(self.presetLower, self.presetUpper):
            raise InvalidParameter(fnName, 'preset_index', preset_index)
        preset_index = self._zeroPadPreset(preset_index)
        cmd = "M{value}".format(value=preset_index)
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^s{value}$".format(value=preset_index)
        responses = {
            "s{value}".format(value=preset_index): True
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)

    def setPanTiltPosition(self, pan: int, tilt: int, speed: int = 29, select: int = 2):
        '''
        Moves the camera to the 

            Parameters:
                    pan (int): an int between 0 and 65535
                    tilt (int): an int between 0 and 65535
                    speed (int): an int between 0 and 30 inclusive
                    select (int): 0 for slow, 2 for fast
            Returns:
                    True if the command executed successfully. otherwise false
            Raises:
                    InvalidParameter
        '''
        fnName = "setPanTiltposition"

        # catch out of bounds here
        if not (self.panLower <= pan < self.panUpper):
            raise InvalidParameter(fnName, 'pan', pan)
        if not (self.tiltLower <= tilt < self.tiltUpper):
            raise InvalidParameter(fnName, 'tilt', tilt)
        if not (0 <= speed < 30):
            raise InvalidParameter(fnName, 'speed', speed)
        if select not in {0, 2}:
            raise InvalidParameter(fnName, 'select', select)

        pan_hex = hex(round(pan))[2:]
        tilt_hex = hex(round(tilt))[2:]
        speed_hex = hex(speed)[2:]

        if len(pan_hex) < 4:
            pan_hex = self._zeroPad(value=pan_hex, desired_length=4)
        if len(tilt_hex) < 4:
            tilt_hex = self._zeroPad(value=tilt_hex, desired_length=4)

        pan_hex = pan_hex.upper()
        tilt_hex = tilt_hex.upper()
        speed_hex = speed_hex.upper()

        cmd = f"APS{pan_hex}{tilt_hex}{speed_hex}{select}"
        url_cmd = self.command_string.format(cmd=cmd)
        response = f"aPS{pan_hex}{tilt_hex}{speed_hex}{select}"
        response_pattern = f"^{response}$"
        responses = {
            response: True
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)

    def getPanTiltPosition(self):
        '''
        Moves the camera to the 

            Parameters:
                    pan (int): an int between 0 and 65535
                    tilt (int): an int between 0 and 65535
            Returns:
                    a touple containing the pan and tilt values or None. The values will be ints between 0 and 65535
            Raises:
                    CommandFailed
        '''
        fnName = "getPanTiltPosition"
        cmd = "APC"
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^aPC([0-9A-F]{4})([0-9A-F]{4})$"
        default = None
        response = self._executeQueryCommand(fnName=fnName, 
                                             cmd=url_cmd,
                                             default=default)
        if response is None:
            raise CommandFailed(fnName, self.address)
        match = re.match(response_pattern, response)
        if match:
            return (int(match.group(1), 16), int(match.group(2), 16))
        return default

    def setZoom(self, zoom):
        '''
        Moves the camera to the 

            Parameters:
                    zoom (int): an int between 1365 and 4095

            Returns:
                    True if the command executed successfully. Otherwise False
            
            Raises:
                    InvalidParameter
        '''
        fnName = "setZoom"
        if type(zoom) is not int or not (self.zoomLower <= zoom < self.zoomUpper):
            raise InvalidParameter(fnName, 'zoom', zoom)

        zoom_hex = hex(round(zoom))[2:]

        if len(zoom_hex) < 3:
            zoom_hex = self._zeroPad(value=zoom_hex, desired_length=3)

        zoom_hex = zoom_hex.upper()

        cmd = "AXZ{zoom}".format(zoom=zoom_hex)
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^axz{zoom}$".format(zoom=zoom_hex)
        responses = {
            "axz{zoom}".format(zoom=zoom_hex): True
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)

    def getZoom(self):
        '''
        Gets the zoom value

            Returns:
                    an int representing the zoom value
            Raises:
                    CommandFailed
        '''
        fnName = "getZoom"
        cmd = "GZ"
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^gz([0-9A-F]{3})$"
        default = None
        response = self._executeQueryCommand(fnName=fnName, 
                                             cmd=url_cmd,
                                             default=default)
        if response is None:
            raise CommandFailed(fnName, self.address)
        match = re.match(response_pattern, response)
        if match:
            return int(match.group(1), 16)
        return default

    def setAutoFocus(self, value):
        '''
        sets Auto Focus

            Parameters:
                 value (bool): a bool where True means turn on and False means turn off
            Returns:
                    True if the command executed successfully. Otherwise False
            Raises:
                    InvalidParameter
        '''
        fnName = "setAutoFocus"
        if type(value) is not bool:
            raise InvalidParameter(fnName, 'value', value)
        cmd = "D1{setting}".format(setting=1 if value else 0)
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^d1([0-1]{1})$"
        responses = {
            "d10": True if not value else False,
            "d11": True if value else False
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                        cmd=url_cmd,
                                        responses=responses,
                                        response_pattern=response_pattern,
                                        default=default)

    def getAutoFocus(self):
        '''
        Gets the zoom value

            Returns:
                    an int representing the zoom value
            Raises:
                    CommandFailed
        '''
        fnName = "getAutoFocus"
        cmd = "D1"
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^d1([0-1]{1})$"
        default = None
        response = self._executeQueryCommand(fnName=fnName, 
                                             cmd=url_cmd,
                                             default=default)
        if response is None:
            raise CommandFailed(fnName, self.address)
        match = re.match(response_pattern, response)
        if match:
            return 'On' if int(match.group(1)) == 1 else "Off"
        return default

'''    def getFocus(self):
        pass

    def setFocus(self, focus):
        pass'''
