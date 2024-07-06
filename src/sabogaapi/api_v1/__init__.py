from fastapi import FastAPI

from sabogaapi.api_v1.routers import (
    boardgames,
    collections,
    user_collections,
    user_plays,
)
from sabogaapi.api_v1.schemas import UserCreate, UserRead, UserUpdate
from sabogaapi.api_v1.users import bearer_backend, cookie_backend, fastapi_users

api_v1 = FastAPI()


@api_v1.get("/hello")
def hello_world() -> str:
    return "Hello World!"


api_v1.include_router(boardgames.router)
api_v1.include_router(collections.router)


api_v1.include_router(
    fastapi_users.get_auth_router(bearer_backend), prefix="/auth/bearer", tags=["Auth"]
)
api_v1.include_router(
    fastapi_users.get_auth_router(cookie_backend), prefix="/auth", tags=["Auth"]
)
api_v1.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
api_v1.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["Auth"],
)
user_router = fastapi_users.get_users_router(UserRead, UserUpdate)
user_router.include_router(user_collections.router)
user_router.include_router(user_plays.router)

api_v1.include_router(
    user_router,
    prefix="/users",
    tags=["Users"],
)
