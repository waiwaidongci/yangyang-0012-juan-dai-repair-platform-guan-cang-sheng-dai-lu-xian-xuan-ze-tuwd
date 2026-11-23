def rights_catalog(cx):
    return {
        "reels":cx.execute("SELECT code,recording,donation FROM acetate_reels WHERE NOT calibration ORDER BY code").fetchall(),
        "grants":cx.execute("""
            SELECT g.*, (g.stage='approved' AND (now() AT TIME ZONE 'Asia/Shanghai')::date BETWEEN begins AND expires) AS usable
            FROM recording_use_grants g ORDER BY g.reel,g.id DESC
        """).fetchall()
    }

def partner_grant(cx, reel, identifier):
    return cx.execute("""
        SELECT * FROM recording_use_grants
        WHERE reel=%s AND id=%s AND access_scope='partner' AND stage='approved'
        AND (now() AT TIME ZONE 'Asia/Shanghai')::date BETWEEN begins AND expires
    """,(reel,identifier)).fetchone()

def seed(cx):
    cx.execute("""
        INSERT INTO recording_use_grants
            (reel,instrument_ref,access_scope,begins,expires,credit_line,documented_by,stage,approved_by)
        SELECT code,'CAT-YT26-INTERNAL','internal','2026-01-01','2031-12-31',
            '潮声档案馆，旧站报时带，内部参考','operator@demo.local','approved','reviewer@demo.local'
        FROM acetate_reels WHERE code='YT-26' ON CONFLICT DO NOTHING
    """)
