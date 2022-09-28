
import prometheus_client
import structlog as logging

from fastapi import Depends, FastAPI, Header, HTTPException, routing, Request
from fastapi.responses import JSONResponse
from fastapi.logger import logger as fastapi_logger
from fastapi_utils.tasks import repeat_every
from prometheus_client import Gauge
from starlette.middleware.cors import CORSMiddleware
from starlette_prometheus import metrics, PrometheusMiddleware

from . import exceptions, routers, models, logging_config, utilities

from .config import config

logger = logging.getLogger(__name__)

logger.info("creating fastapi")
api = FastAPI()

logging_config.inject_request_id(api)

logger.info("adding prometheus middleware")
api.add_middleware(PrometheusMiddleware)
api.add_route("/metrics/", metrics)

hb = Gauge('netsocadmin_heartbeat', 'Unixtime Netsoc Cloud heartbeat')

# dump stack traces on timeout/kill
import faulthandler
faulthandler.enable()

utilities.yaml.use_prettier_multiline_strings()

@api.on_event("startup")
@repeat_every(seconds=1)
def heartbeat():
    hb.set_to_current_time()


logger.info("setting up routers")
api.include_router(
    routers.accounts.router,
    prefix='/v1/accounts',
    tags=['accounts']
)

api.include_router(
    routers.signups.router,
    prefix='/v1/signups',
    tags=['signups']
)

api.include_router(
    routers.proxmox.router,
    prefix='/v1/proxmox',
    tags=['proxmox']
)

"""
Return a Rest error model whenever our API throws exceptions.rest.Error
"""
@api.exception_handler(exceptions.rest.Error)
def resterror_exception_handler(request: Request, e: exceptions.rest.Error):
    return JSONResponse(
        status_code=e.status_code,
        content=e.error_model.dict(),
    )

"""
Return a Rest error model whenever our API throws 
"""
@api.exception_handler(exceptions.exception.APIException)
def resterror_exception_handler(request: Request, e: Exception):
    logger.exception(f"API exception (500)", e=e, exc_info=True)

    return JSONResponse(
        status_code=500,
        content=models.rest.Error(
            detail=models.rest.Detail(
                msg=str(e)
            )
        ).dict()
    )

"""
Mask general exceptions
"""
@api.exception_handler(Exception)
def exception_handler(request: Request, e: Exception):
    logger.error(f"Unhandled exception", e=e, exc_info=True)

    if config.production:
        return JSONResponse(
            status_code=500,
            content=models.rest.Error(
                detail=models.rest.Detail(
                    msg=f"An unexpected error occured"
                )
            ).dict()
        )
    else:
        return JSONResponse(
            status_code=500,
            content=models.rest.Error(
                detail=models.rest.Detail(
                    msg=f"Exception: {type(e)}: {e}"
                )
            ).dict()
        )

"""
Simplify operation IDs so that generated API clients have simpler function
names.

Should be called only after all routes have been added.
"""
for route in api.routes:
    if isinstance(route, routing.APIRoute):
        route.operation_id = route.name 

"""
Disable cross-origin
"""
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["location"]
)
