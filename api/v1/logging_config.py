
import structlog
import uuid

from fastapi import FastAPI, Request

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)

def inject_request_id(api: FastAPI):
    structlog.configure(
        processors=[
            merge_contextvars,
            structlog.processors.KeyValueRenderer(),
        ]
    )

    @api.middleware("http")
    async def add_context_logging(request: Request, call_next):
        clear_contextvars()

        request_id = str(uuid.uuid4())

        bind_contextvars(request_id=request_id)

        response = await call_next(request)
        clear_contextvars()

        response.headers["X-Request-ID"] = request_id
        return response
  
