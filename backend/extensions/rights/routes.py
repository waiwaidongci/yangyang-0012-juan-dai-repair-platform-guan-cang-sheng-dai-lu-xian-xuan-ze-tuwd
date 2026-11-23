from fastapi import APIRouter, Depends
from core import db, require
from extensions.delivery.service import recall_for_revoked_grant
from .read_model import rights_catalog
from .schemas import Revocation, UseGrant
from .service import approve, record, revoke

router = APIRouter(prefix="/api/tape-rights")

@router.get("")
def catalog(user=Depends(require())):
    with db() as cx:
        return rights_catalog(cx)

@router.post("",status_code=201)
def save(data: UseGrant,user=Depends(require("operator"))):
    with db() as cx:
        return record(cx,data,user["email"])

@router.post("/{identifier}/approve")
def accept(identifier: int,user=Depends(require("reviewer"))):
    with db() as cx:
        return approve(cx,identifier,user["email"])

@router.post("/{identifier}/revoke")
def rescind(identifier: int,reason: Revocation,user=Depends(require("reviewer"))):
    with db() as cx:
        item = revoke(cx,identifier,reason.note,user["email"])
        # 同一事务内把该授权下已出库的清单转入待召回
        item["recalled_handoffs"] = [row["id"] for row in recall_for_revoked_grant(cx,identifier)]
        return item
