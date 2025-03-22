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

