from fastapi import HTTPException
from extensions.rights.read_model import partner_grant
from extensions.rights.service import lock_reel
from .read_model import derivative_identity

def usable_copy(cx, identifier):
    copy = derivative_identity(cx,identifier)
    if not copy or copy["stage"]!="accepted" or copy["kind"]!="access":
        raise HTTPException(409,"馆际交付须使用已通过质检的访问副本")
    return copy

def prepare(cx,data,actor):
    copy = usable_copy(cx,data.derivative)
    lock_reel(cx,copy["reel"])
    grant = partner_grant(cx,copy["reel"],data.grant_id)
    if not grant:
        raise HTTPException(409,"需要同一馆藏卷的当前馆际授权")
    partner = cx.execute("SELECT * FROM archive_exchange_partners WHERE slug=%s",(data.partner,)).fetchone()
    if not partner or not partner["supports_access_copy"]:
        raise HTTPException(409,"伙伴接入范围不涵盖访问副本")
    return cx.execute("""
        INSERT INTO recording_handoffs(derivative,grant_id,partner,purpose,created_by,seal_digest,credit_text)
        VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *
    """,(copy["id"],grant["id"],data.partner,data.purpose,actor,
         copy["measured_digest"],grant["credit_line"])).fetchone()

def handoff_for_update(cx, identifier):
    valid = cx.execute("SELECT derivative FROM recording_handoffs WHERE id=%s",(identifier,)).fetchone()
    if not valid:
        raise HTTPException(404,"交付清单不存在")
    copy = usable_copy(cx,valid["derivative"])
    lock_reel(cx,copy["reel"])
    item = cx.execute("SELECT * FROM recording_handoffs WHERE id=%s FOR UPDATE",(identifier,)).fetchone()
    return copy,item

def release(cx, identifier, actor):
    copy,item = handoff_for_update(cx,identifier)
    if item["stage"]!="prepared":
        raise HTTPException(409,"只有准备中的清单可办理出库")
    if not partner_grant(cx,copy["reel"],item["grant_id"]):
        raise HTTPException(409,"授权在出库前失效或撤回，须撤单重建")
    return cx.execute("""
        UPDATE recording_handoffs SET stage='sent',released_by=%s,released_at=now() WHERE id=%s RETURNING *
    """,(actor,identifier)).fetchone()

def receive(cx, identifier, receipt):
    _,item = handoff_for_update(cx,identifier)
    if item["stage"]!="sent" or item["seal_digest"]!=receipt.verified_digest:
        raise HTTPException(409,"清单未出库，或签收校验值与封套不一致")
    return cx.execute("""
        UPDATE recording_handoffs SET stage='acknowledged',receipt_ref=%s,received_at=now() WHERE id=%s RETURNING *
    """,(receipt.receipt_ref,identifier)).fetchone()

def withdraw(cx, identifier):
    handoff_for_update(cx,identifier)
    row = cx.execute("""
        UPDATE recording_handoffs SET stage='withdrawn' WHERE id=%s AND stage='prepared' RETURNING *
    """,(identifier,)).fetchone()
    if not row:
        raise HTTPException(409,"只有待出库清单可撤销")
    return row
