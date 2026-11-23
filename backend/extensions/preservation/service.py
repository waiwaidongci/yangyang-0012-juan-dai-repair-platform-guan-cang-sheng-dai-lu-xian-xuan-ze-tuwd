from decimal import Decimal

from fastapi import HTTPException

def metadata_rules(manifest):
    notes = []
    if manifest["expected_digest"]!=manifest["measured_digest"]:
        notes.append("入档清单与实测 SHA-256 不一致")
    if abs(manifest["duration_seconds"]-manifest["target_seconds"])>Decimal(".5"):
        notes.append("与馆藏时长差超过半秒")
    if manifest["channels"]!=manifest["target_channels"]:
        notes.append("声道数与采集登记不符")
    allowed = (96000,192000) if manifest["kind"]=="master" else (44100,48000)
    if manifest["sample_rate"] not in allowed:
        notes.append("采样率与入档用途不匹配")
    if manifest["clipped_frames"]:
        notes.append("采集报告含削波帧")
    return notes

def submit(cx,data,actor):
    card = cx.execute("""
        SELECT c.stage FROM conservation_cards c JOIN signal_excerpts s ON s.code=c.excerpt
        JOIN reel_capture_profiles p ON p.reel=s.reel WHERE c.id=%s
    """,(data.card,)).fetchone()
    if not card or card["stage"]!="authorised":
        raise HTTPException(409,"请选已签发且有采集规格的工序卡")
    return cx.execute("""
        INSERT INTO audio_derivative_checks
          (card,kind,filename,expected_digest,measured_digest,duration_seconds,
           sample_rate,channels,clipped_frames,recorded_by)
        VALUES (%(card)s,%(kind)s,%(filename)s,%(expected_digest)s,%(measured_digest)s,
                %(duration_seconds)s,%(sample_rate)s,%(channels)s,%(clipped_frames)s,%(actor)s)
        RETURNING *
    """,data.model_dump()|{"actor":actor}).fetchone()

def verify(cx, identifier, actor):
    result = cx.execute("""
        SELECT d.*,p.target_seconds,p.target_channels FROM audio_derivative_checks d
        JOIN conservation_cards c ON c.id=d.card JOIN signal_excerpts s ON s.code=c.excerpt
        JOIN reel_capture_profiles p ON p.reel=s.reel WHERE d.id=%s FOR UPDATE OF d
    """,(identifier,)).fetchone()
    if not result:
        raise HTTPException(404,"质检记录不存在")
    if result["stage"]!="queued":
        raise HTTPException(409,"请创建新一版派生件记录供复测")
    notes = metadata_rules(result)
    return cx.execute("""
        UPDATE audio_derivative_checks SET stage=%s,review_by=%s,failed_rules=%s WHERE id=%s RETURNING *
    """,("failed" if notes else "accepted",actor,notes,identifier)).fetchone()
