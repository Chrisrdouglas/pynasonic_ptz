class CommandFailed(BaseException):
    def __init__(self, command, address):
        self.command = command
        self.address = address
        super().__init__()

    def __str__(self):
        return "{0} failed to get a response from {1}".format(self.command,
                                                              self.address)

class InvalidParameter(BaseException):
    def __init__(self, command, param_name, value):
        self.command = command
        self.param_name = param_name
        self.value = value
        super().__init__()

    def __str__(self):
        return "{0} does not accept {1} for {2}".format(self.command,
                                                        self.value,
                                                        self.param_name)

class InvalidCamera(BaseException):
    def __init__(self, value):
        self.value = value
        super().__init__()

    def __str__(self):
        return "{0} is not a valid camera. To see a list of valid cameras please check cameras.py".format(self.value)
