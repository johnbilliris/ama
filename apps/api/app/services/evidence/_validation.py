from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError


def reject_unknown_query_params(request: Request) -> None:
    route = request.scope.get("route")
    dependant = getattr(route, "dependant", None)
    allowed = {field.alias for field in getattr(dependant, "query_params", ()) if getattr(field, "alias", None)}
    unknown = sorted(set(request.query_params) - allowed)
    if not unknown:
        return

    raise RequestValidationError(
        [
            {
                "type": "extra_forbidden",
                "loc": ("query", field),
                "msg": "Extra inputs are not permitted",
                "input": request.query_params.get(field),
            }
            for field in unknown
        ]
    )
