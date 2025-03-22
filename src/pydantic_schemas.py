from pydantic import BaseModel
from typing import  Union
from datetime import datetime

class ShortenURLModelResponse(BaseModel):
    status: str
    shorten_url: str


class ShortenURLModelRequest(BaseModel):
    url: str
    custom_alias: Union[str, None] = None
    expires_at: Union[datetime, None] = None


class ShortCodeStatsResponse(BaseModel):
    initial_url: str
    redirect_count: int
    created_at: Union[datetime, None]
    last_used_at: Union[datetime, None]