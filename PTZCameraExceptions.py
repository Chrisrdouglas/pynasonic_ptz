class UnsupportedPTZOperation(BaseException):
    def __init__(self, camera, fnName):
        self.camera = camera
        self.fnName = fnName
        super().__init__()
        
    def __str__(self):
        return "{0} does not support {1}".format(self.camera, self.fnName)


class UnsupportedCamera(BaseException):
    def __init__(self, camera):
        self.camera = camera
        super().__init__()
        
    def __str__(self):
        return "{0} is not a supported camera".format(self.camera)

class CommandFailed(BaseException):
    def __init__(self, command, address):
        self.command = command
        self.address = address
        super().__init__()
        
    def __str__(self):
        return "{0} failed to get a response from {1}".format(self.command, self.address)
