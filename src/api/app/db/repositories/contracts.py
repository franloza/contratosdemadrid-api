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

    def get_contract_adapter(self, contract: dict):
        contract = dict(contract)
        contract["_source"]["numero-sogi"] = contract["_source"]["numero-expediente"]
        contract["_source"]["duración"] = '- meses'
        contract["_source"]["fecha-inicio-de-ejecucion"] = contract["_source"]["fecha-formalizacion"]
        contract["_source"]["licitadores"] = 1
        contract["_source"]["url"] = "http://www.madrid.org/cs/Satellite?cid=1224915242285&language=es&pagename=PortalContratacion%2FPage%2FPCON_buscadorAvanzado"
        return contract

