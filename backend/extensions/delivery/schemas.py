from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing_extensions import Annotated
from extensions.preservation.schemas import Digest

class Manifest(BaseModel):
    derivative: int = Field(gt=0)
    grant_id: int = Field(gt=0)
    partner: str = Field(max_length=30)
    purpose: Annotated[str,StringConstraints(strip_whitespace=True,min_length=6,max_length=180)]

class Receipt(BaseModel):
    """伙伴离线回执：签收与退回确认共用结构，signed_at 是对方离线记录的时间。"""
    receipt_ref: str = Field(pattern=r"^[A-Z0-9-]{5,32}$")
    verified_digest: Digest
    signed_at: datetime

    @field_validator("signed_at")
    @classmethod
    def not_from_future(cls, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        if value > datetime.now(timezone.utc)+timedelta(minutes=5):
            raise ValueError("回执时间不能晚于当前时间")
        return value

class Reissue(BaseModel):
    grant_id: int = Field(gt=0)
    purpose: Annotated[str,StringConstraints(strip_whitespace=True,min_length=6,max_length=180)]
