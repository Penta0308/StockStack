CREATE TABLE IF NOT EXISTS companies
(
    cid         SERIAL PRIMARY KEY,
    name        TEXT UNIQUE,
    cash        BIGINT NOT NULL DEFAULT 50000000,
    worktype    INT    NOT NULL,
    factorysize INT    NOT NULL DEFAULT 1,
    inventory   FLOAT4 ARRAY[2] DEFAULT ARRAY [0.0, 0.0]
);

INSERT INTO companies (cid, name, worktype)
VALUES (0, 'CONSUMER', 0)
ON CONFLICT (cid) DO NOTHING;

CREATE TABLE IF NOT EXISTS stocks
(
    ticker       TEXT PRIMARY KEY,
    cid          INT REFERENCES companies (cid) UNIQUE,
    totalamount  INT DEFAULT 0    NOT NULL,
    parvalue     INT DEFAULT 5000 NOT NULL,
    closingprice INT DEFAULT 5000 NOT NULL
);

CREATE TABLE IF NOT EXISTS traders
(
    tid  BIGINT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS stockowns
(
    tid    BIGINT REFERENCES traders (tid),
    ticker TEXT REFERENCES stocks (ticker),
    amount INT DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS orders
(
    tid    BIGINT REFERENCES traders (tid),
    ticker TEXT REFERENCES stocks (ticker),
    amount INT NOT NULL,
    price  INT
);

CREATE TABLE IF NOT EXISTS config
(
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO config (key, value)
VALUES ('market_variancerate_float', '0.3'),
       ('market_pricestepsize_fe', $$1 /1000 5 /5000 10 /10000 50 /50000 100 /100000 500 /500000 1000$$),
       ('market_tickn', '0')
ON CONFLICT (key) DO NOTHING;
