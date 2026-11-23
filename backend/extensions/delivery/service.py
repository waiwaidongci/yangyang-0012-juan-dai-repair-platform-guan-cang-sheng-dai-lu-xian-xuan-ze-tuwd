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

def recall_for_revoked_grant(cx, grant_id):
    """授权撤回时，该授权下已出库的副本转入待召回，等待退回确认或晚到回执。"""
    return cx.execute("""
        UPDATE recording_handoffs SET stage='recalling',recalled_at=now()
        WHERE grant_id=%s AND stage='sent' RETURNING id
    """,(grant_id,)).fetchall()

def receipt_retry(cx, identifier, kind, receipt):
    """同一回执重试：返回已登记事实，不新增记录；编号相同内容不同则冲突。"""
    existing = cx.execute(
        "SELECT * FROM handoff_receipts WHERE receipt_ref=%s",(receipt.receipt_ref,)
    ).fetchone()
    if not existing:
        return None
    same = (existing["handoff"]==identifier and existing["kind"]==kind
            and existing["verified_digest"]==receipt.verified_digest
            and existing["signed_at"]==receipt.signed_at)
    if not same:
        raise HTTPException(409,"回执编号已登记，内容不一致")
    return existing

def record_receipt(cx, identifier, kind, receipt, actor, disputed=False, note=None):
    return cx.execute("""
        INSERT INTO handoff_receipts(handoff,kind,receipt_ref,verified_digest,signed_at,recorded_by,disputed,dispute_note)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
    """,(identifier,kind,receipt.receipt_ref,receipt.verified_digest,
         receipt.signed_at,actor,disputed,note)).fetchone()

def receive(cx, identifier, receipt, actor):
    """登记签收回执。撤回前签收的仍归原单；撤回后签收的保留事实并标争议。"""
    _,item = handoff_for_update(cx,identifier)
    retry = receipt_retry(cx,identifier,'acknowledgement',receipt)
    if retry:
        return {"handoff":item,"receipt":retry,"duplicated":True}
    if item["stage"] not in ("sent","recalling","acknowledged","returned"):
        raise HTTPException(409,"清单未出库，不能登记签收回执")
    if item["seal_digest"]!=receipt.verified_digest:
        raise HTTPException(409,"签收校验值与封套不一致")
    grant = cx.execute(
        "SELECT revoked_at FROM recording_use_grants WHERE id=%s",(item["grant_id"],)
    ).fetchone()
    disputed,note = False,None
    if grant["revoked_at"] and receipt.signed_at>grant["revoked_at"]:
        disputed,note = True,"签收时间晚于授权撤回时间"
    elif item["stage"]=="acknowledged":
        disputed,note = True,"清单已有有效签收，此回执待核对"
    row = record_receipt(cx,identifier,'acknowledgement',receipt,actor,disputed,note)
    if not disputed and item["stage"] in ("sent","recalling"):
        item = cx.execute("""
            UPDATE recording_handoffs SET stage='acknowledged',receipt_ref=%s,received_at=now()
            WHERE id=%s RETURNING *
        """,(receipt.receipt_ref,identifier)).fetchone()
    return {"handoff":item,"receipt":row,"duplicated":False}

def confirm_return(cx, identifier, receipt, actor):
    """登记退回确认。退回与签收可同时提交，两条事实都保留在回执记录里。"""
    _,item = handoff_for_update(cx,identifier)
    retry = receipt_retry(cx,identifier,'return',receipt)
    if retry:
        return {"handoff":item,"receipt":retry,"duplicated":True}
    recalled = item["stage"]=="recalling" or (item["stage"]=="acknowledged" and item["recalled_at"])
    if not recalled:
        raise HTTPException(409,"清单不在待召回状态，不能登记退回确认")
    if item["seal_digest"]!=receipt.verified_digest:
        raise HTTPException(409,"退回校验值与封套不一致")
    row = record_receipt(cx,identifier,'return',receipt,actor)
    item = cx.execute("""
        UPDATE recording_handoffs SET stage='returned',returned_at=now() WHERE id=%s RETURNING *
    """,(identifier,)).fetchone()
    return {"handoff":item,"receipt":row,"duplicated":False}

def reissue(cx, identifier, data, actor):
    """退回确认后凭新授权补发。补发单是独立清单，不被原单的旧回执改写。"""
    copy,item = handoff_for_update(cx,identifier)
    if item["stage"]!="returned":
        raise HTTPException(409,"收到退回确认后才可凭新授权补发")
    if cx.execute("SELECT 1 FROM recording_handoffs WHERE reissue_of=%s",(identifier,)).fetchone():
        raise HTTPException(409,"该清单已开立补发单")
    grant = partner_grant(cx,copy["reel"],data.grant_id)
    if not grant:
        raise HTTPException(409,"需要同一馆藏卷的当前馆际授权")
    return cx.execute("""
        INSERT INTO recording_handoffs(derivative,grant_id,partner,purpose,created_by,seal_digest,credit_text,reissue_of)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
    """,(item["derivative"],grant["id"],item["partner"],data.purpose,actor,
         item["seal_digest"],grant["credit_line"],identifier)).fetchone()

def withdraw(cx, identifier):
    handoff_for_update(cx,identifier)
    row = cx.execute("""
        UPDATE recording_handoffs SET stage='withdrawn' WHERE id=%s AND stage='prepared' RETURNING *
    """,(identifier,)).fetchone()
    if not row:
        raise HTTPException(409,"只有待出库清单可撤销")
    return row
