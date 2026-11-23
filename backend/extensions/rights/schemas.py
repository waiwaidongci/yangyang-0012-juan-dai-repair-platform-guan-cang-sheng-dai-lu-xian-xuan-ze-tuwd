from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

Credit = Annotated[str,StringConstraints(strip_whitespace=True,min_length=4,max_length=220)]

class UseGrant(BaseModel):
    reel: str = Field(max_length=30)
    instrument_ref: str = Field(pattern=r"^[A-Z0-9-]{5,30}$")
    access_scope: Literal["internal","partner","public"]
    begins: date
    expires: date
    credit_line: Credit

class Revocation(BaseModel):
    note: Credit
