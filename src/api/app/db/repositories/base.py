from elasticsearch import AsyncElasticsearch


class BaseRepository:
    def __init__(self, client: AsyncElasticsearch) -> None:
        self._client = client

    @property
    def client(self) -> AsyncElasticsearch:
        return self._client
