from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.isos import router as isos_router
from app.api.recipes import router as recipes_router
from app.api.builds import router as builds_router
from app.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(isos_router, prefix="/isos", tags=["isos"])
api_router.include_router(recipes_router, prefix="/recipes", tags=["recipes"])
api_router.include_router(builds_router, prefix="/builds", tags=["builds"])