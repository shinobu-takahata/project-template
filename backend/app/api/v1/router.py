from fastapi import APIRouter

from app.api.v1.endpoints import examples, health, products

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(examples.router, prefix="/examples", tags=["examples"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
