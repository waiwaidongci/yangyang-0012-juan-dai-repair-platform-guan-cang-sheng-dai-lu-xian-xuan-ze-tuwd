from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated
from extensions.preservation.schemas import Digest

class Manifest(BaseModel):
    derivative: int = Field(gt=0)
    grant_id: int = Field(gt=0)
    partner: str = Field(max_length=30)
    purpose: Annotated[str,StringConstraints(strip_whitespace=True,min_length=6,max_length=180)]

class Acknowledgement(BaseModel):
    receipt_ref: str = Field(pattern=r"^[A-Z0-9-]{5,32}$")
    verified_digest: Digest
