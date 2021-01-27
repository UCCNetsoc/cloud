
import structlog
import uuid

from fastapi import FastAPI, Request

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    merge_contextvars,
    unbind_contextvars,
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "plain_console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
        "key_value": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.KeyValueRenderer(key_order=['timestamp', 'level', 'event', 'logger']),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "plain_console",
        },
        "json_file": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": "json.log",
            "formatter": "json_formatter",
        },
        "flat_line_file": {
            "class": "logging.handlers.WatchedFileHandler",
            "filename": "flat_line.log",
            "formatter": "key_value",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console", "flat_line_file", "json_file"],
            "level": "INFO"
        },

        "app2": {
            "handlers": ["console", "flat_line_file", "json_file"],
            "level": "WARN"
        },

        "app3": {
            "handlers": ["console", "flat_line_file", "json_file"],
            "level": "DEBUG"
        },
    }
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.ExceptionPrettyPrinter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)



def inject_request_id(api: FastAPI):
    # structlog.configure(
    #     processors=[
    #         merge_contextvars,
    #         structlog.processors.KeyValueRenderer()
    #     ]
    # )

    @api.middleware("http")
    async def add_context_logging(request: Request, call_next):
        clear_contextvars()

        request_id = str(uuid.uuid4())

        bind_contextvars(request_id=request_id)

        response = await call_next(request)
        clear_contextvars()

        response.headers["X-Request-ID"] = request_id
        return response
  
