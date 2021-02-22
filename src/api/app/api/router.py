from fastapi import APIRouter

from . import companies, contracts, main

router = APIRouter()
router.include_router(companies.router, tags=["companies"], prefix="/companies")
router.include_router(contracts.router, tags=["contracts"], prefix="/contracts")
router.include_router(main.router, tags=["main"])
