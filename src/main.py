from fastapi import Depends, FastAPI, Request
from db import User
from schemas import UserCreate, UserRead, UserUpdate
from users import auth_backend, current_active_user, fastapi_users
from router1 import router as router1
from router2 import router as router2
import uvicorn

import logging

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

from redis import asyncio as aioredis

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

app = FastAPI(lifespan=lifespan)


# Middleware для логирования
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Логируем информацию о запросе
    logger.info(f"Request: {request.method} {request.url}")

    # Обрабатываем запрос и получаем ответ
    response = await call_next(request)

    # Логируем информацию о ответе
    logger.info(f"Response status: {response.status_code}")

    return response


app.include_router(router1)

app.include_router(router2)

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


@app.get("/authenticated-route")
async def authenticated_route(users: User = Depends(current_active_user)):
    print(users)
    print(users.registered_at)
    print(users.email)
    return {"message": f"Hello {users.email}!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)