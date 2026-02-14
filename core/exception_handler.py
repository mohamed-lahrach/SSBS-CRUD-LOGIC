from django.db.models import ProtectedError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from buses.models import Bus
from routes.models import Route
from trips.models import Trip

from .exceptions import DomainError, IntegrityError


def _protected_error_message(exc):
    try:
        obj = next(iter(exc.protected_objects))
    except Exception:
        return "Cannot delete object with protected dependencies"

    if isinstance(obj, Bus):
        return "Cannot delete bus assigned to routes"
    if isinstance(obj, Route):
        return "Cannot delete route with existing trips"
    if isinstance(obj, Trip):
        return "Cannot delete trip with existing reservations"
    return "Cannot delete object with protected dependencies"


def api_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        return Response(
            {"error": exc.message, "code": exc.code},
            status=exc.status_code,
        )

    if isinstance(exc, ProtectedError):
        err = IntegrityError(
            message=_protected_error_message(exc),
            code="protected_delete",
        )
        return Response(
            {"error": err.message, "code": err.code},
            status=err.status_code,
        )

    return drf_exception_handler(exc, context)
