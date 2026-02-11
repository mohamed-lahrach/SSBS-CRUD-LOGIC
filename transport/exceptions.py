from rest_framework import status


class DomainError(Exception):
    default_message = "Domain error"
    default_code = "domain_error"
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message=None, code=None, status_code=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        super().__init__(self.message)


class LifecycleError(DomainError):
    default_message = "Invalid lifecycle operation"
    default_code = "lifecycle_error"
    status_code = status.HTTP_400_BAD_REQUEST


class FreezeError(DomainError):
    default_message = "Object is frozen and cannot be modified"
    default_code = "freeze_error"
    status_code = status.HTTP_409_CONFLICT


class CapacityError(DomainError):
    default_message = "Capacity exceeded"
    default_code = "capacity_error"
    status_code = status.HTTP_409_CONFLICT


class IntegrityError(DomainError):
    default_message = "Integrity constraint violated"
    default_code = "integrity_error"
    status_code = status.HTTP_409_CONFLICT
