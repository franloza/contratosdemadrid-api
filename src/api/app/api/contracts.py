from fastapi import APIRouter, Depends

from api.app.api.dependencies.database import get_repository
from api.app.db.repositories.contracts import ContractsRepository

router = APIRouter()

@router.get(
    '/latest',
    response_model=dict,
    name="contracts:latest"
)
async def get_latest_contracts(
    contracts_repo: ContractsRepository = Depends(get_repository(ContractsRepository)),
) -> dict:
    contracts = await contracts_repo.get_latest_contracts()
    return contracts

@router.get(
    '/count',
    response_model=dict,
    name="contracts:count"
)
async def count(
        contracts_repo: ContractsRepository = Depends(get_repository(ContractsRepository)),
) -> dict:
    return {"count": (await contracts_repo.count())["count"]}


@router.get(
    '/{contract_id}',
    response_model=dict,
    name="contracts:get-contract"
)
async def get_contract(
    contract_id: str,
    contracts_repo: ContractsRepository = Depends(get_repository(ContractsRepository)),
) -> dict:
    contracts = await contracts_repo.get_contract(contract_id)
    if len(contracts["hits"]["hits"]) > 0:
        contract = contracts_repo.get_contract_adapter(contracts["hits"]["hits"][0])
    else:
        contract = {}
    return contract





