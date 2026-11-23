def seed_reels(cx):
    for n,name in enumerate(("港岸口述","冬夜访谈","电台交班"),1):
        donation = f"COLL-{n}"
        for suffix, label, values in (
            ("C","clean",[(2,0,7),(3,1,8)]),
            ("M","mend",[(4,8,2),(6,7,3)]),
            ("R","rehouse",[(17,1,0),(20,0,1)]),
        ):
            reel = f"{donation}-{suffix}"
            cx.execute("INSERT INTO acetate_reels VALUES (%s,%s,%s,true) ON CONFLICT DO NOTHING",(reel,name,donation))
            for index, (drops,snaps,dust) in enumerate(values,1):
                cx.execute(
                    "INSERT INTO signal_excerpts VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    (f"{reel}-{index}",reel,index*25,11 if n == 3 and suffix == "R" and index == 2 else drops+n-1,snaps,dust,label),
                )
    cx.execute("INSERT INTO acetate_reels VALUES ('YT-26','旧站报时带','CITY-04',false) ON CONFLICT DO NOTHING")
    cx.execute("""INSERT INTO signal_excerpts VALUES ('YT26-120','YT-26',120,15,1,2,NULL) ON CONFLICT DO NOTHING""")
