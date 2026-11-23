from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

Digest = Annotated[str,StringConstraints(pattern=r"^[a-f0-9]{64}$")]

class Derivative(BaseModel):
    card: int = Field(gt=0)
    kind: Literal["master","access"]
    filename: str = Field(pattern=r"^[0-9A-Za-z_-]{2,70}\.(wav|flac)$")
    expected_digest: Digest
    measured_digest: Digest
    duration_seconds: Decimal = Field(gt=0,le=14400,max_digits=8,decimal_places=2)
    sample_rate: Literal[44100,48000,96000,192000]
    channels: Literal[1,2]
    clipped_frames: int = Field(ge=0,le=10000000)
