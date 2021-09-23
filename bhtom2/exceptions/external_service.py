class ExternalServiceException(RuntimeError):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class NoResultException(ExternalServiceException):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidExternalServiceStatusException(ExternalServiceException):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidExternalServiceResponseException(ExternalServiceException):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)