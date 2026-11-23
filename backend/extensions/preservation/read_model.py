def profile_work(cx):
    return cx.execute("""
        SELECT c.id,c.excerpt,c.stage,s.reel,p.target_seconds,p.target_channels FROM conservation_cards c
        JOIN signal_excerpts s ON s.code=c.excerpt JOIN reel_capture_profiles p ON p.reel=s.reel
        ORDER BY c.id DESC
    """).fetchall()

def quality_board(cx):
    return {"work":profile_work(cx),"checks":cx.execute("""
        SELECT a.*,s.reel FROM audio_derivative_checks a
        JOIN conservation_cards c ON c.id=a.card JOIN signal_excerpts s ON s.code=c.excerpt ORDER BY a.id DESC
    """).fetchall()}

def seed(cx):
    cx.execute("""
        INSERT INTO reel_capture_profiles SELECT code,480,1 FROM acetate_reels WHERE code='YT-26'
        ON CONFLICT DO NOTHING
    """)
