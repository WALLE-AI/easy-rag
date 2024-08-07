class BaseServiceError(Exception):
    def __init__(self, description: str = None):
        self.description = description


class FileNotExistsError(BaseServiceError):
    pass


class FileTooLargeError(BaseServiceError):
    description = "{message}"


class UnsupportedFileTypeError(BaseServiceError):
    pass
