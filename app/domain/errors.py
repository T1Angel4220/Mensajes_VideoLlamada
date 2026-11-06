class ValidationError(ValueError):
    pass


class AuthLockedError(ValidationError):
    pass


class UnauthorizedError(Exception):
    pass


class NotFoundError(ValidationError):
    pass


class ForbiddenError(ValidationError):
    pass
