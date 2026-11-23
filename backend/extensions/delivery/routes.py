from fastapi import APIRouter, Depends
from core import db, require
from .read_model import exchange_desk
from .schemas import Acknowledgement, Manifest
from .service import prepare, receive, release, withdraw

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
def ack(identifier: int,data: Acknowledgement,user=Depends(require("operator"))):
    with db() as cx:
        return receive(cx,identifier,data)

@router.post("/{identifier}/withdraw")
def remove(identifier: int,user=Depends(require("reviewer"))):
    with db() as cx:
        return withdraw(cx,identifier)
