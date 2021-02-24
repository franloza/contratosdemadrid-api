import dateutil.parser

from fastapi import APIRouter, Depends

from api.app.api.dependencies.database import get_repository
from api.app.db.repositories.companies import CompaniesRepository

router = APIRouter()


@router.get(
    '/top',
    response_model=dict,
    name="contracts:top"
)
async def get_top_companies(
    companies_repo: CompaniesRepository = Depends(get_repository(CompaniesRepository)),
) -> dict:
    companies = await companies_repo.get_top_companies()
    buckets = []
    for idx, company in enumerate(companies["aggregations"]["contracts"]["total"]["buckets"]):
        company_info = await companies_repo.get_company_awardings(company["key"], limit=1)
        if company_info["hits"]["hits"] and company_info["hits"]["hits"][0]:
            bucket = companies["aggregations"]["contracts"]["total"]["buckets"][idx]
            bucket["company"] = company_info["hits"]["hits"][0]["inner_hits"]["adjudicatario"]
            buckets.append(bucket)
    companies["aggregations"]["contracts"]["total"]["buckets"] = buckets
    return companies


@router.get(
    '/{company_id}',
    response_model=dict,
    name="companies:get-company"
)
async def get_company(
    company_id: str,
    companies_repo: CompaniesRepository = Depends(get_repository(CompaniesRepository)),
) -> dict:
    return {
        "company": await companies_repo.get_company(company_id),
        "contracts": await companies_repo.get_company_contracts(company_id),
        "competitors": {
            "took": 0,
            "timed_out": False,
            "_shards": {
                "total": 1,
                "successful": 1,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": {
                    "value": 0,
                    "relation": "eq"
                },
                "max_score": 0,
                "hits": []
                }
            },
        "candidacies": [],
        "histogram": """<svg viewBox="0 0 250 200" preserveAspectRatio="none"></svg>"""
        }
