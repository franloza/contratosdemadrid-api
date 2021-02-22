from typing import List

from fastapi import APIRouter, Depends

from api.app.api.dependencies.database import get_repository
from api.app.db.repositories.companies import CompaniesRepository
from api.app.db.repositories.contracts import ContractsRepository

router = APIRouter()


@router.get(
    '/search',
    response_model=List[dict],
    name="main:search"
)
async def search(
    q: str,
    companies_repo: CompaniesRepository = Depends(get_repository(CompaniesRepository)),
    contracts_repo: ContractsRepository = Depends(get_repository(ContractsRepository)),
) -> List[dict]:
    result = []
    companies = await companies_repo.search_company(q)
    for company in companies["hits"]["hits"]:
        company["type"] = "company"
        result.append({"hit": company})
    contracts = await contracts_repo.search_contracts(q)
    for contract in contracts["hits"]["hits"]:
        contract["type"] = "contract"
        result.append({"hit": contracts_repo.get_contract_adapter(contract)})
    return result
