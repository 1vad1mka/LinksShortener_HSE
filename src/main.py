from fastapi import Depends, FastAPI
from src.db import User
from src.schemas import UserCreate, UserRead, UserUpdate
from src.users import auth_backend, current_active_user, fastapi_users
from src.router1 import router as router1
import uvicorn

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from redis import asyncio as aioredis

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(router1)

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

import time

@app.get("/hello")
@cache(expire=60)
async def hello():
    time.sleep(5)
    return 'Hello!'

@app.get("/authenticated-route")
async def authenticated_route(users: User = Depends(current_active_user)):
    print(users)
    print(users.registered_at)
    print(users.email)
    return {"message": f"Hello {users.email}!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)