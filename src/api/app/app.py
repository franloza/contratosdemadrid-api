from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .api.router import router
from .core.config import API_PREFIX, DEBUG, PROJECT_NAME, VERSION, ALLOWED_HOSTS
from .core.events import create_start_app_handler, create_stop_app_handler


def get_application() -> FastAPI:
    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_event_handler("startup", create_start_app_handler(application))
    application.add_event_handler("shutdown", create_stop_app_handler(application))

    application.include_router(router, prefix=API_PREFIX)

    return application
