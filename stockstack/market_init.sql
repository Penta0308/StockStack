CREATE SCHEMA IF NOT EXISTS market;
CREATE SCHEMA IF NOT EXISTS world;

CREATE TABLE IF NOT EXISTS world.goods
(
    gid       INT PRIMARY KEY,
    name      TEXT   NOT NULL DEFAULT 'Unnamed',
    baseprice FLOAT4 NOT NULL DEFAULT 0,
    decayrate FLOAT4 NOT NULL DEFAULT 0
);

INSERT INTO world.goods (gid, name, baseprice, decayrate)
VALUES (0, 'Labor', 200, 1.0),
       (1, 'Agricultural products', 55, 0.1),
       (2, 'Crude Oil', 100, 0.03),
       (3, 'Metal', 120, 0.0),
       (4, 'Grocery', 110, 0.5),
       (5, 'Clothing', 100, 0.01),
       (6, 'Fuel', 130, 0.06),
       (7, 'Chemicals', 100, 0.1),
       (8, 'Electronics', 300, 0.01)
ON CONFLICT (gid) DO NOTHING;
INSERT INTO world.goods (gid)
VALUES (9),
       (10),
       (11),
       (12),
       (13),
       (14),
       (15)
ON CONFLICT (gid) DO NOTHING;


CREATE TABLE IF NOT EXISTS world.factories
(
    worktype INT PRIMARY KEY,
    consume  INT ARRAY[16] NOT NULL DEFAULT ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    produce  INT ARRAY[16] NOT NULL DEFAULT ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
);

INSERT INTO world.factories (worktype, consume, produce)
VALUES (0, -- 0번 특수공장: 소비자
        ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]::INT[],
        ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]::INT[])
ON CONFLICT (worktype) DO NOTHING;

CREATE TABLE IF NOT EXISTS market.companies
(
    cid         SERIAL PRIMARY KEY,
    name        TEXT UNIQUE   NOT NULL,
    worktype    INT REFERENCES world.factories (worktype) DEFAULT NULL,
    factorysize INT           NOT NULL                    DEFAULT 0,
    inventory   INT ARRAY[16] NOT NULL                    DEFAULT ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    outventory  INT ARRAY[16] NOT NULL                    DEFAULT ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    sellprice   INT ARRAY[16] NOT NULL                    DEFAULT ARRAY [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    listable    BOOL          NOT NULL                    DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS market.stocks
(
    ticker       TEXT PRIMARY KEY,
    cid          INT REFERENCES market.companies (cid) UNIQUE,
    totalamount  INT DEFAULT 0    NOT NULL,
    parvalue     INT DEFAULT 5000 NOT NULL,
    closingprice INT DEFAULT 5000 NOT NULL
);

CREATE TABLE IF NOT EXISTS market.stockowns
(
    company BIGINT REFERENCES market.companies (cid),
    ticker  TEXT REFERENCES market.stocks (ticker),
    amount  INT DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS market.orders
(
    company BIGINT REFERENCES market.companies (cid),
    ticker  TEXT REFERENCES market.stocks (ticker),
    amount  INT NOT NULL,
    price   INT
);

CREATE TABLE IF NOT EXISTS world.config
(
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO world.config (key, value)
VALUES ('market_variancerate_float', '0.3'),
       ('market_pricestepsize_fe', $$1 /1000 5 /5000 10 /10000 50 /50000 100 /100000 500 /500000 1000$$),
       ('market_interestrate', '0.05'),
       ('market_tickn', '0')
ON CONFLICT (key) DO NOTHING;
