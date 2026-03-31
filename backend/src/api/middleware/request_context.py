from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('x-correlation-id', str(uuid4()))
        request.state.correlation_id = correlation_id

        started = perf_counter()
        response = await call_next(request)
        duration_ms = int((perf_counter() - started) * 1000)

        response.headers['x-correlation-id'] = correlation_id
        response.headers['x-duration-ms'] = str(duration_ms)
        return response
