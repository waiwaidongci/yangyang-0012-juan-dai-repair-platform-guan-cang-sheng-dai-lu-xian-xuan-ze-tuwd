def derivative_identity(cx, identifier):
    return cx.execute("""
        SELECT d.*,s.reel FROM audio_derivative_checks d
        JOIN conservation_cards c ON c.id=d.card JOIN signal_excerpts s ON s.code=c.excerpt
        WHERE d.id=%s
    """,(identifier,)).fetchone()

def exchange_desk(cx):
    return {
        "partners":cx.execute("SELECT * FROM archive_exchange_partners ORDER BY slug").fetchall(),
        "derivatives":cx.execute("""
            SELECT d.id,d.filename,e.reel FROM audio_derivative_checks d
            JOIN conservation_cards c ON c.id=d.card JOIN signal_excerpts e ON e.code=c.excerpt
            WHERE d.kind='access' AND d.stage='accepted' ORDER BY d.id DESC
        """).fetchall(),
        "grants":cx.execute("""
            SELECT id,reel,instrument_ref,credit_line FROM recording_use_grants
            WHERE stage='approved' AND access_scope='partner'
            AND (now() AT TIME ZONE 'Asia/Shanghai')::date BETWEEN begins AND expires
            ORDER BY reel,id DESC
        """).fetchall(),
        "handoffs":cx.execute("""
            SELECT h.*,p.name,d.filename,g.instrument_ref FROM recording_handoffs h
            JOIN archive_exchange_partners p ON p.slug=h.partner
            JOIN audio_derivative_checks d ON d.id=h.derivative
            JOIN recording_use_grants g ON g.id=h.grant_id ORDER BY h.id DESC
        """).fetchall()
    }

def seed(cx):
    cx.execute("""
        INSERT INTO archive_exchange_partners VALUES
          ('RIVER','河湾地方史档案室',true),('DESK','北岸目录协作组',false)
        ON CONFLICT DO NOTHING
    """)
