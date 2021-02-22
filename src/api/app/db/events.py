from fastapi import FastAPI
from elasticsearch import AsyncElasticsearch
from loguru import logger

from ..core.config import DATABASE_HOST, DATABASE_PORT


async def connect_to_db(app: FastAPI) -> None:
    logger.info(f"Connecting to {DATABASE_HOST}:{DATABASE_PORT}")
    app.state.db = AsyncElasticsearch([{'host': DATABASE_HOST, 'port': DATABASE_PORT}])
    logger.debug(await app.state.db.info())
    logger.info("Connection established")


async def close_db_connection(app: FastAPI) -> None:
    logger.info("Closing connection to database")
    try:
        await app.state.db.close()
    except TypeError:
        pass
    logger.info("Connection closed")
