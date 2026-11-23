from fastapi import HTTPException

def lock_reel(cx, reel):
    row = cx.execute("SELECT * FROM acetate_reels WHERE code=%s FOR UPDATE",(reel,)).fetchone()
    if not row:
        raise HTTPException(404,"馆藏卷未登记")
    return row

def record(cx, permit, actor):
    reel = lock_reel(cx,permit.reel)
    if reel["calibration"]:
        raise HTTPException(409,"参考带的内部标签不能转为外部使用授权")
    if permit.expires<permit.begins:
        raise HTTPException(422,"授权截止日早于生效日")
    return cx.execute("""
        INSERT INTO recording_use_grants(reel,instrument_ref,access_scope,begins,expires,credit_line,documented_by)
        VALUES (%(reel)s,%(instrument_ref)s,%(access_scope)s,%(begins)s,%(expires)s,%(credit_line)s,%(actor)s)
        RETURNING *
    """,permit.model_dump()|{"actor":actor}).fetchone()

def permit_for_update(cx, identifier):
    permit = cx.execute("SELECT reel FROM recording_use_grants WHERE id=%s",(identifier,)).fetchone()
    if not permit:
        raise HTTPException(404,"授权记录不存在")
    lock_reel(cx,permit["reel"])
    return cx.execute("SELECT * FROM recording_use_grants WHERE id=%s FOR UPDATE",(identifier,)).fetchone()

def approve(cx, identifier, actor):
    item = permit_for_update(cx,identifier)
    if item["stage"]!="draft":
        raise HTTPException(409,"只能签认草稿授权")
    conflict = cx.execute("""
        SELECT instrument_ref FROM recording_use_grants WHERE id<>%s AND reel=%s AND access_scope=%s
          AND stage='approved' AND begins<=%s AND expires>=%s
    """,(identifier,item["reel"],item["access_scope"],item["expires"],item["begins"])).fetchone()
    if conflict:
        raise HTTPException(409,"同用途已有重叠期间的有效授权，请核对来源")
    return cx.execute("""
        UPDATE recording_use_grants SET stage='approved',approved_by=%s WHERE id=%s RETURNING *
    """,(actor,identifier)).fetchone()

def revoke(cx, identifier, note, actor):
    permit_for_update(cx,identifier)
    item = cx.execute("""
        UPDATE recording_use_grants SET stage='revoked',revoke_note=%s,revoked_by=%s
        WHERE id=%s AND stage='approved' RETURNING *
    """,(note,actor,identifier)).fetchone()
    if not item:
        raise HTTPException(409,"只可撤回已签授权")
    return item
