CREATE SCHEMA IF NOT EXISTS world;

CREATE TABLE IF NOT EXISTS world.factories
(
    fid       INT PRIMARY KEY,
    consume   JSONB NOT NULL DEFAULT '{}',
    produce   JSONB NOT NULL DEFAULT '{}',
    unitprice INT   NOT NULL DEFAULT 0
);

INSERT INTO world.factories (fid, produce, unitprice)
VALUES (0, '{
  "labor": 1
}'::JSONB, 0)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS world.config
(
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO world.config (key, value)
VALUES ('world_interestrate', '0.05'),
       ('market_tick_active', 'False'),
       ('market_tick_n', '0')
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS world.companies
(
    cid      SERIAL PRIMARY KEY,
    name     TEXT UNIQUE NOT NULL,
    worktype INT                  DEFAULT NULL,
    listable BOOL        NOT NULL DEFAULT FALSE,
    board    JSONB       NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS world.companyfactories
(
    cid         INT REFERENCES world.companies (cid),
    fid         INT REFERENCES world.factories (fid) DEFAULT NULL,
    factorysize INT   NOT NULL                       DEFAULT 0,
    efficiency  FLOAT NOT NULL                       DEFAULT 1.0,
    UNIQUE (cid, fid)
);


