import logging
from typing import List

from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings

API_PREFIX = "/v1"

VERSION = "0.1.0"

config = Config(".env")

DEBUG: bool = config("DEBUG", cast=bool, default=False)

PROJECT_NAME: str = config("PROJECT_NAME", default="contratosdemadrid")
ALLOWED_HOSTS: List[str] = config(
    "ALLOWED_HOSTS", cast=CommaSeparatedStrings, default=""
)

# Database configuration
DATABASE_HOST: str = config("DATABASE_HOST", default="localhost")
DATABASE_PORT: str = config("DATABASE_HOST", default="9200")
COMPANIES_INDEX_NAME: str = "companies"
CONTRACTS_INDEX_NAME: str = "contracts"

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
