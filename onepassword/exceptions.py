class OnePasswordException(Exception):
    """
    Base exception class for 1Password exceptions
    """


class OnePasswordCLINotFound(OnePasswordException):
    """
    Raise an exception when the 1password-cli client is not available locally
    """

    def __init__(self, msg) -> None:
        self.msg = msg


class OnePasswordValueNotFound(OnePasswordException):
    """
    A generic exception for when a value cannot be found in 1Password
    """

    def __init__(self, msg) -> None:
        self.msg = msg


class OnePasswordJSONError(OnePasswordException):
    """
    A generic exception for anything to do with JSON Encoding or Decoding contents pertaining to a
    1Password resource.
    """

    def __init__(self, msg) -> None:
        self.msg = msg


class OnePasswordRuntimeError(OnePasswordException):
    """
    A generic exception for anything to do with the execution or runtime of 1Password commands
    """

    def __init__(self, msg) -> None:
        self.msg = msg
