
import prometheus_client
import structlog as logging

from fastapi import Depends, FastAPI, Header, HTTPException, routing, Request
from fastapi.responses import JSONResponse
from fastapi.logger import logger as fastapi_logger
from fastapi_utils.tasks import repeat_every
from prometheus_client import Gauge
from starlette.middleware.cors import CORSMiddleware
from starlette_prometheus import metrics, PrometheusMiddleware

from . import exceptions, routers, models, webserver_configurator, homedir_consistency, logging_config

from .config import config

logger = logging.getLogger(__name__)

logger.info("creating fastapi")
api = FastAPI()

logging_config.inject_request_id(api)

logger.info("adding prometheus middleware")
api.add_middleware(PrometheusMiddleware)
api.add_route("/metrics/", metrics)

hb = Gauge('netsocadmin_heartbeat', 'Unixtime Netsoc Admin heartbeat')

@api.on_event("startup")
@repeat_every(seconds=1)
def heartbeat():
    hb.set_to_current_time()

@api.on_event("startup")
@repeat_every(seconds=config.webserver_configurator.push_interval)
def run_configurator():
    logger.info("webserver_configurator began running")
    try:
        webserver_configurator.configure()
        logger.info("webserver_configurator finished running")
    except Exception as e:
        logging.error("webserver_configurator had an exception while running", e=e, exc_info=True)

@api.on_event("startup")
@repeat_every(seconds=config.homedir_consistency.scan_interval)
def run_homedir_consistency():
    try:
        logger.info("homedir_consistency began running")
        homedir_consistency.ensure()
        logger.info("homedir_consistency finished running")
    except Exception as e:
        logging.error("homedir_consistency had an exception while running", e=e, exc_info=True)

@api.on_event("startup")
def start_metrics():
    try:
        prometheus_client.start_http_server(config.metrics.port)
    except Exception as e:
        logging.getLogger("v1.metrics").error(e,exc_info=True)


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
    routers.backups.router,
    prefix='/v1/backups',
    tags=['backups']
)

api.include_router(
    routers.mysql.router,
    prefix='/v1/mysql',
    tags=['mysql']
)

api.include_router(
    routers.mentorships.router,
    prefix='/v1/mentorships',
    tags=['mentorships']
)

api.include_router(
    routers.websites.router,
    prefix='/v1/websites',
    tags=['websites']
)

"""
Return a Rest error model whenever our API throws exceptions.rest.Error
"""
@api.exception_handler(exceptions.rest.Error)
async def resterror_exception_handler(request: Request, e: exceptions.rest.Error):
    return JSONResponse(
        status_code=e.status_code,
        content=e.error_model.dict(),
    )

"""
Return a Rest error model whenever our API throws 
"""
@api.exception_handler(exceptions.exception.APIException)
async def resterror_exception_handler(request: Request, e: Exception):
    logger.error(f"API exception (500)", e=e, exc_info=True)

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
async def exception_handler(request: Request, e: Exception):
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
