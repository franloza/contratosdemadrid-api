from ...core.config import CONTRACTS_INDEX_NAME
from ...db.repositories.base import BaseRepository


class ContractsRepository(BaseRepository):

    async def search_contracts(self, query: str) -> dict:
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body={
            "query": {
                "query_string": {
                  "query": query,
                  "analyze_wildcard": True,
                  "default_field": "*"
                }
            }
        })

    async def count(self) -> dict:
        return await self.client.count(index=CONTRACTS_INDEX_NAME, human=True)

    async def get_contract(self, contract_id):
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body={
            "query": {
                "terms": {
                    "_id": [contract_id]
                }
            }
        })

    async def get_latest_contracts(self):
        return await self.client.search(index=CONTRACTS_INDEX_NAME, body={
          "query": {
            "match_all": {}
          },
          "size": 25,
          "sort": [
            {
              "fecha-formalizacion": {
                "order": "desc"
              }
            }
          ]
        })


