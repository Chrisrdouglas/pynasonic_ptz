from requests import get
from requests.exceptions import Timeout
import re

import constants
from PTZCameraExceptions import UnsupportedCamera, UnsupportedPTZOperation, CommandFailed, InvalidParameter

class PTZCamera:
    def __init__(self, camera=constants.DEFAULT_CAMERA, address=constants.DEFUALT_IP, protocol=constants.DEFAULT_PROTOCOL):
        self.camera = camera
        self.address = address
        if self.camera not in constants.SUPPORTED_CAMERAS:
            raise UnsupportedCamera(self.camera)
        self.command_string = "{protocol}://{address}/cgi-bin/aw_ptz?cmd=%23{cmd}&res=1".format(protocol=protocol, address=self.address, cmd="{cmd}")
        #self.commands = constants.CAMERAS[camera]['commands']
        #self.responses = constants.CAMERAS[camera]['responses']
    
    def _formatURL(self,fnName, value=None):
        if value is None:
            return self.command_string.format(cmd=self.commands[fnName]["cmd"])
        return self.command_string.format(cmd=self.commands[fnName]["cmd"].format(value=value))

    '''def _formatResponse(self, fnName, value=None):
        if not self.commands[fnName]['dynamicResponse']:
            return self.commands[fnName]['response_pattern']
        return self.commands[fnName]['response_pattern'].format(value=value)'''

    def _zeroPad(self, value, desired_length):
        pad_length = desired_length - len(value)
        return "0"*pad_length + value

    def _zeroPadPreset(self, value):
        if value < 10:
            return "0{0}".format(value)
        return str(value)

    def _supportedFunction(self, fn):
        if fn == None:
            return False
        elif self.camera in constants.UNSUPPORTED_CAMERA_FUNCTIONS.keys():
            if fn in constants.UNSUPPORTED_CAMERA_FUNCTIONS[self.camera]:
                return False
        else:
            return True
    
    def _executeCommand(self, fnName, cmd, responses, response_pattern, default):
        response = default
        try:
            if not self._supportedFunction(fnName):
                raise UnsupportedPTZOperation(self.camera, fnName)
            r = get(cmd)
            if r.status_code == 200:
                match = re.match(response_pattern, r.text)
                if match is None:
                    raise CommandFailed(fnName, self.address)
                response = responses.get(r.text, default)
            else:
                raise CommandFailed(fnName, self.address)
        except UnsupportedPTZOperation as e:
            print(e)
        except Timeout as e:
            print(e)
        except CommandFailed as e:
            print(e)
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
        
    def setPowerState(self, cameraPowerState=False):
        '''
        Changes the Power State of the camera

            Parameters:
                    cameraPowerState (int): Desired power state for camera. True for on. False for standby

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
            
    def moveToPreset(self, preset_index=0):
        '''
        Moves camera to a registered preset position

            Parameters:
                    preset_index (int): ID of the preset registered on the camera

            Returns:
                    True if moving to the preset position. otherwise false
        '''
        fnName = "moveToPreset"
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

    def registerPreset(self, preset_index=None):
        '''
        Registers the current position as a preset position for a camera

            Parameters:
                    preset_index (int): ID of the preset registered on the camera

            Returns:
                    True if the position has been registered. otherwise false
        '''
        fnName = "registerPreset"
        if not preset_index:
            raise InvalidParameter(fnName, "preset_index", preset_index)
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
    
    def setPanTiltPosition(self, pan, tilt):
        '''
        Moves the camera to the 

            Parameters:
                    pan (int): an int between 0 and 65536
                    tilt (int): an int between 0 and 65536

            Returns:
                    True if the command executed successfully. otherwise false
        '''
        fnName = "panTiltposition"

        # catch out of bounds here
        if not (0 <= pan <= 65535) and not (0 <= tilt <= 65535):
            # raise OutOfBoundsException()
            return False
        

        pan_hex = hex(round(pan))[2:]
        tilt_hex = hex(round(tilt))[2:]

        if len(pan_hex) < 4:
            pan_hex = self._zeroPad(value=pan_hex, desired_length=4)
        if len(tilt_hex) < 4:
            tilt_hex = self._zeroPad(value=tilt_hex, desired_length=4)
        
        pan_hex = pan_hex.upper()
        tilt_hex = tilt_hex.upper()

        cmd = "APC{pan}{tilt}".format(pan=pan_hex,tilt=tilt_hex)
        url_cmd = self.command_string.format(cmd=cmd)
        response_pattern = "^aPC{pan}{tilt}$".format(pan=pan_hex,tilt=tilt_hex)
        responses = {
            "aPC{pan}{tilt}".format(pan=pan_hex,tilt=tilt_hex): True
        }
        default = False
        return self._executeCommand(fnName=fnName, 
                                     cmd=url_cmd, 
                                     responses=responses,
                                     response_pattern=response_pattern,
                                     default=default)
    
    def setZoom(self, zoom):
        '''
        Moves the camera to the 

            Parameters:
                    zoom (int): an int between 1365 and 4095

            Returns:
                    True if the command executed successfully. Otherwise False
        '''
        fnName = "setZoom"
        if not (1365 <= zoom <= 4095):
            # raise OutOfBoundsException()
            return False
        

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
