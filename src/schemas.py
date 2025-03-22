import uuid
from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    id: int
    email: str
    username: str


class UserCreate(schemas.BaseUserCreate):
    id: int
    email: str
    username: str
    password: str