from typing import AsyncGenerator, Callable, Type

from fastapi import Depends
from starlette.requests import Request

from elasticsearch import AsyncElasticsearch
from ...db.repositories.base import BaseRepository


def _get_db_client(request: Request) -> AsyncElasticsearch:
    return request.app.state.db


def get_repository(repo_type: Type[BaseRepository]) -> Callable:  # type: ignore
    async def _get_repo(
        client: AsyncElasticsearch = Depends(_get_db_client),
    ) -> AsyncGenerator[BaseRepository, None]:
        yield repo_type(client)
    return _get_repo
