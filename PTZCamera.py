from requests import get
from requests.exceptions import Timeout
import re

import constants
from PTZCameraExceptions import UnsupportedCamera, UnsupportedPTZOperation, CommandFailed

class PTZCamera:
    def __init__(self, camera=constants.DEFAULT_CAMERA, address=constants.DEFUALT_IP, protocol=constants.DEFAULT_PROTOCOL):
        self.camera = camera
        self.address = address
        if self.camera not in constants.CAMERAS.keys():
            raise UnsupportedCamera(self.camera)
        self.commandString = constants.CAMERAS[camera]['commandString'].format(protocol=protocol, address=self.address, cmd="{cmd}")
        self.commands = constants.CAMERAS[camera]['commands']
        #self.responses = constants.CAMERAS[camera]['responses']
    
    def _formatURL(self,fnName, value=None):
        if value is None:
            return self.commandString.format(cmd=self.commands[fnName]["cmd"])
        return self.commandString.format(cmd=self.commands[fnName]["cmd"].format(value=value))

    def _formatResponse(self, fnName, value=None):
        if not self.commands[fnName]['dynamicResponse']:
            return self.commands[fnName]['responsePattern']
        return self.commands[fnName]['responsePattern'].format(value=value)
    
    def _zeroPad(self, value):
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
    
    def getPowerState(self):
        '''
        Reads the power state of the camera

            Returns:
                    A string saying what state the camera is in
        '''
        fnName = "getPowerState"
        try:
            if not self._supportedFunction(fnName):
                raise UnsupportedPTZOperation(self.camera, fnName)
            
            r = get(self._formatURL(fnName=fnName))
            responsePattern = self._formatResponse(fnName=fnName)
            if r.status_code == 200:
                match = re.match(responsePattern, r.text)
                if match is None:
                    raise CommandFailed(fnName, self.address)
                powerstate = self.commands[fnName]['response'][r.text]
            else:
                raise CommandFailed(fnName, self.address)
        
        except UnsupportedPTZOperation as e:
            print(e)
        
        except Timeout as e:
            return self.commands[fnName]['response']['default']
            print(e)
        
        except CommandFailed as e:
            return self.commands[fnName]['response']['default']
            print(e)
        
        return powerstate
        
    def setPowerState(self, cameraPowerState):
        '''
        Returns the sum of two decimal numbers in binary digits.

            Parameters:
                    cameraPowerState (int): Desired power state for camera. 1 for on. 0 for standby

            Returns:
                    A string saying what power state it will be in. On or Standby
        '''
        fnName = "setPowerState"
        try:
            if not self._supportedFunction(fnName):
                raise UnsupportedPTZOperation(self.camera, fnName)
            
            r = get(self._formatURL(fnName=fnName, value=cameraPowerState))
            responsePattern = self._formatResponse(fnName=fnName, value=cameraPowerState)
            if r.status_code == 200:
                match = re.match(responsePattern, r.text)
                if match is None:
                    raise CommandFailed(fnName, self.address)
                powerstate = self.commands[fnName]['response'][r.text]
            else:
                raise CommandFailed(fnName, self.address)
        
        except UnsupportedPTZOperation as e:
            print(e)
        
        except Timeout as e:
            print(e)
            return self.commands[fnName]['response']['default']
            
        
        except CommandFailed as e:
            print(e)
            return self.commands[fnName]['response']['default']
        
        return powerstate
            
    def moveToPreset(self, presetIndex=0):
        '''
        Moves camera to a registered preset position

            Parameters:
                    presetIndex (int): ID of the preset registered on the camera

            Returns:
                    True if moving to the preset position. otherwise false
        '''
        fnName = "moveToPreset"
        presetIndex = self._zeroPad(presetIndex)
        print(presetIndex)
        try: 
            if not self._supportedFunction(fnName):
                raise UnsupportedPTZOperation(self.camera, fnName)
            
            r = get(self._formatURL(fnName=fnName, value=presetIndex))
            responsePattern = self._formatResponse(fnName=fnName, value=presetIndex)
            if r.status_code == 200:
                match = re.search(responsePattern, r.text)
                if match is None:
                    raise CommandFailed(fnName, self.address)

        except UnsupportedPTZOperation as e:
            print(e)
            return False
        
        except Timeout as e:
            print(e)
            return False
        
        except CommandFailed as e:
            print(e)
            return False
        
        return True

    def registerPreset(self, presetIndex=None):
        pass