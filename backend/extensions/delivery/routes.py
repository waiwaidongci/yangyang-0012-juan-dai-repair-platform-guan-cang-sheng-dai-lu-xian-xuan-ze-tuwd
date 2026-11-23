from fastapi import APIRouter, Depends
from core import db, require
from .read_model import exchange_desk
from .schemas import Manifest, Receipt, Reissue
from .service import confirm_return, prepare, receive, reissue, release, withdraw

router = APIRouter(prefix="/api/archive-handoffs")

@router.get("")
def view(user=Depends(require())):
    with db() as cx:
        return exchange_desk(cx)

@router.post("",status_code=201)
def pack(data: Manifest,user=Depends(require("operator"))):
    with db() as cx:
        return prepare(cx,data,user["email"])

@router.post("/{identifier}/release")
def send(identifier: int,user=Depends(require("reviewer"))):
    with db() as cx:
        return release(cx,identifier,user["email"])

@router.post("/{identifier}/receipt")
def ack(identifier: int,data: Receipt,user=Depends(require("operator"))):
    with db() as cx:
        return receive(cx,identifier,data,user["email"])

@router.post("/{identifier}/return")
def send_back(identifier: int,data: Receipt,user=Depends(require("operator"))):
    with db() as cx:
        return confirm_return(cx,identifier,data,user["email"])

@router.post("/{identifier}/reissue",status_code=201)
def resend(identifier: int,data: Reissue,user=Depends(require("operator"))):
    with db() as cx:
        return reissue(cx,identifier,data,user["email"])

@router.post("/{identifier}/withdraw")
def remove(identifier: int,user=Depends(require("reviewer"))):
    with db() as cx:
        return withdraw(cx,identifier)
