CREATE TABLE IF NOT EXISTS acetate_reels (
    code text PRIMARY KEY,
    recording text NOT NULL,
    donation text NOT NULL,
    calibration bool NOT NULL DEFAULT false
);
CREATE TABLE IF NOT EXISTS signal_excerpts (
    code text PRIMARY KEY,
    reel text NOT NULL REFERENCES acetate_reels(code),
    start_second integer NOT NULL CHECK(start_second >= 0),
    dropout integer NOT NULL CHECK(dropout BETWEEN 0 AND 30),
    snaps integer NOT NULL CHECK(snaps BETWEEN 0 AND 20),
    residue integer NOT NULL CHECK(residue BETWEEN 0 AND 9),
    known_route text CHECK(known_route IN ('clean','mend','rehouse')),
    UNIQUE(reel,start_second)
);
CREATE TABLE IF NOT EXISTS evaluation_manifests (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label text UNIQUE NOT NULL,
    job bigint REFERENCES app_jobs(id),
    report jsonb
);
CREATE TABLE IF NOT EXISTS holdout_assignments (
    evaluation bigint REFERENCES evaluation_manifests(id),
    excerpt text REFERENCES signal_excerpts(code),
    fold smallint NOT NULL CHECK(fold BETWEEN 1 AND 3),
    PRIMARY KEY(evaluation,excerpt)
);
CREATE TABLE IF NOT EXISTS conservation_cards (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    excerpt text UNIQUE NOT NULL REFERENCES signal_excerpts(code),
    evaluation bigint NOT NULL REFERENCES evaluation_manifests(id),
    route text CHECK(route IN ('clean','mend','rehouse')),
    stage text NOT NULL DEFAULT 'proposed' CHECK(stage IN ('proposed','authorised')),
    explanation text NOT NULL,
    authoriser text
);
