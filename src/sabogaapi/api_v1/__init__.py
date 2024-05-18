from fastapi import Depends, FastAPI

from sabogaapi.api_v1.database import User
from sabogaapi.api_v1.routers import boardgames, plays
from sabogaapi.api_v1.schemas import UserCreate, UserRead, UserUpdate
from sabogaapi.api_v1.users import auth_backend, current_active_user, fastapi_users

api_v1 = FastAPI()


@api_v1.get("/hello")
def hello_world() -> str:
    return "Hello World!"


api_v1.include_router(boardgames.router)
api_v1.include_router(plays.router)


api_v1.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
api_v1.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
api_v1.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
api_v1.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
api_v1.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
