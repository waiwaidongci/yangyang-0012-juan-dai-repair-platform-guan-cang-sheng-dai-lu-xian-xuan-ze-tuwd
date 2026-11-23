from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

from core import db, enqueue, require
from model_choice import METHODS, ROUTE_LABELS, compare
from reel_seed import seed_reels

router = APIRouter(prefix="/api/tapes")

class Measurement(BaseModel):
    start_second: int = Field(ge=0,le=86400)
    dropout: int = Field(ge=0,le=30)
    snaps: int = Field(ge=0,le=20)
    residue: int = Field(ge=0,le=9)

class Assignment(BaseModel):
    excerpt: str = Field(min_length=1,max_length=50)
    fold: int = Field(ge=1,le=3)

class Manifest(BaseModel):
    label: str = Field(min_length=1,max_length=60)
    assignments: list[Assignment] = Field(min_length=6,max_length=60)

class Card(BaseModel):
    excerpt: str = Field(min_length=1,max_length=50)
    evaluation: int = Field(gt=0)

def rows_for(cx,evaluation):
    return cx.execute("""
        SELECT signal_excerpts.*,acetate_reels.donation,holdout_assignments.fold
        FROM holdout_assignments JOIN signal_excerpts ON signal_excerpts.code=excerpt
        JOIN acetate_reels ON acetate_reels.code=signal_excerpts.reel
        WHERE evaluation=%s ORDER BY signal_excerpts.code
    """,(evaluation,)).fetchall()

def validate(rows):
    by_donor = defaultdict(set)
    by_fold = defaultdict(set)
    all_routes = set(ROUTE_LABELS)
    for row in rows:
        by_donor[row["donation"]].add(row["fold"])
        by_fold[row["fold"]].add(row["known_route"])
    leaked = [donation for donation, folds in by_donor.items() if len(folds)>1]
    if leaked:
        raise HTTPException(409, f"同一捐赠批跨折泄漏：{', '.join(sorted(leaked))}")
    if len(by_fold) < 2 or any(routes != all_routes for routes in by_fold.values()):
        raise HTTPException(409,"至少两折，每折必须包含三个工序的签认样段")

@router.get("/catalog")
def catalog(user=Depends(require())):
    with db() as cx:
        reels = cx.execute("SELECT * FROM acetate_reels ORDER BY calibration,code").fetchall()
        readings = cx.execute("""
            SELECT signal_excerpts.*,acetate_reels.donation FROM signal_excerpts
            JOIN acetate_reels ON acetate_reels.code=reel ORDER BY reel,start_second
        """).fetchall()
        manifests = cx.execute("SELECT * FROM evaluation_manifests ORDER BY id DESC LIMIT 30").fetchall()
        cards = cx.execute("SELECT * FROM conservation_cards ORDER BY id DESC").fetchall()
    return {"reels":reels,"readings":readings,"manifests":manifests,"cards":cards}

@router.post("/reels/{code}/excerpt",status_code=201)
def log_excerpt(code: str, data: Measurement,user=Depends(require("operator"))):
    with db() as cx:
        reel = cx.execute("SELECT * FROM acetate_reels WHERE code=%s",(code,)).fetchone()
        if not reel:
            raise HTTPException(404,"音带卷不存在")
        if reel["calibration"]:
            raise HTTPException(409,"已封存的训练盘不接收新的未签认样段")
        sample = f"{code.replace('-','')}-{data.start_second}"
        cx.execute(
            "INSERT INTO signal_excerpts VALUES (%s,%s,%s,%s,%s,%s,NULL)",
            (sample,code,data.start_second,data.dropout,data.snaps,data.residue),
        )
    return {"code":sample}

@router.post("/manifests",status_code=202)
def submit_manifest(data: Manifest,user=Depends(require("reviewer"))):
    codes = [item.excerpt for item in data.assignments]
    if len(set(codes)) != len(codes):
        raise HTTPException(409,"复验清单中有重复样段")
    with db() as cx:
        catalog_rows = cx.execute("""
            SELECT signal_excerpts.*,acetate_reels.donation
            FROM signal_excerpts JOIN acetate_reels ON acetate_reels.code=reel
            WHERE signal_excerpts.code=ANY(%s) AND known_route IS NOT NULL AND calibration
        """,(codes,)).fetchall()
        if len(codes) != len(catalog_rows):
            raise HTTPException(409,"清单中有未签认或不属于参考库的样段")
        assignment = {item.excerpt:item.fold for item in data.assignments}
        validate([row | {"fold":assignment[row["code"]]} for row in catalog_rows])
        version = cx.execute("INSERT INTO evaluation_manifests(label) VALUES (%s) RETURNING id",(data.label,)).fetchone()["id"]
        for item in data.assignments:
            cx.execute("INSERT INTO holdout_assignments VALUES (%s,%s,%s)",(version,item.excerpt,item.fold))
        job = enqueue(cx,"reel-validation",{"id":version})
        cx.execute("UPDATE evaluation_manifests SET job=%s WHERE id=%s",(job,version))
    return {"id":version,"job_id":job}

def run_job(cx,kind,payload):
    if kind != "reel-validation":
        raise ValueError(kind)
    version = payload["id"]
    rows = rows_for(cx,version)
    validate(rows)
    report = compare(rows)
    cx.execute("UPDATE evaluation_manifests SET report=%s WHERE id=%s",(Jsonb(report),version))
    return report

@router.post("/cards",status_code=201)
def propose(data: Card,user=Depends(require("operator"))):
    with db() as cx:
        evidence = cx.execute("""
            SELECT signal_excerpts.* FROM signal_excerpts JOIN acetate_reels ON acetate_reels.code=reel
            WHERE signal_excerpts.code=%s AND NOT calibration
        """,(data.excerpt,)).fetchone()
        model = cx.execute("SELECT * FROM evaluation_manifests WHERE id=%s",(data.evaluation,)).fetchone()
        if not evidence or not model or not model["report"]:
            raise HTTPException(409,"需待处理样段与已完成的分折复验")
        route, explanation = METHODS[model["report"]["selected"]](evidence,rows_for(cx,data.evaluation))
        if model["report"]["accuracy"][model["report"]["selected"]] < .6:
            raise HTTPException(409,"分折均值低于 60%，转人工选择路线")
        row = cx.execute("""
            INSERT INTO conservation_cards(excerpt,evaluation,route,explanation)
            VALUES (%s,%s,%s,%s) RETURNING *
        """,(data.excerpt,data.evaluation,route,explanation)).fetchone()
    return row

@router.post("/cards/{card}/authorise")
def authorise(card: int,user=Depends(require("reviewer"))):
    with db() as cx:
        row = cx.execute("""
            UPDATE conservation_cards SET stage='authorised',authoriser=%s
            WHERE id=%s AND stage='proposed' RETURNING *
        """,(user["email"],card)).fetchone()
        if not row:
            raise HTTPException(409,"仅待审工序卡可签发")
    return row

def seed(cx):
    seed_reels(cx)
    record = cx.execute("""
        INSERT INTO evaluation_manifests(label) VALUES ('分藏批复验 · 对照样组')
        ON CONFLICT DO NOTHING RETURNING id
    """).fetchone()
    if record:
        version = record["id"]
        cx.execute("""
            INSERT INTO holdout_assignments(evaluation,excerpt,fold)
            SELECT %s,signal_excerpts.code,RIGHT(donation,1)::smallint
            FROM signal_excerpts JOIN acetate_reels ON acetate_reels.code=reel WHERE calibration
        """,(version,))
        run_job(cx,"reel-validation",{"id":version})
