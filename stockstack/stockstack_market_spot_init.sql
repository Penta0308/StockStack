CREATE TABLE IF NOT EXISTS lconfig
(
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO lconfig (key, value)
VALUES ('market_variancerate_float', '1.0'),
       ('market_pricestepsize_fe', $$1 /1000 5 /5000 10 /10000 50 /50000 100 /100000 500 /500000 1000$$)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS stocks
(
    ticker       TEXT PRIMARY KEY,
    name         TEXT UNIQUE      NOT NULL,
    cid          INT DEFAULT 0,
    parvalue     INT DEFAULT 0    NOT NULL,
    closingprice INT DEFAULT 5000 NOT NULL,
    lastprice    INT DEFAULT 5000 NOT NULL
);

CREATE TABLE IF NOT EXISTS stockowns
(
    cid    INT REFERENCES world.companies (cid),
    ticker TEXT REFERENCES stocks (ticker),
    amount INT DEFAULT 0 NOT NULL,
    CONSTRAINT stockowns_cid_ticker_constraint UNIQUE (cid, ticker)
);

CREATE TABLE IF NOT EXISTS stockorders
(
    ots    INT PRIMARY KEY,
    cid    INT REFERENCES world.companies (cid),
    ticker TEXT REFERENCES stocks (ticker),
    amount INT NOT NULL,
    price INT
);
CREATE TABLE IF NOT EXISTS stockorderspending
(
    ots    SERIAL PRIMARY KEY,
    cid    INT REFERENCES world.companies (cid),
    ticker TEXT REFERENCES stocks (ticker),
    amount INT NOT NULL,
    price  INT,
    CONSTRAINT stockorderspending_cid_ticker_constraint UNIQUE (cid, ticker)
);

INSERT INTO stocks (ticker, name, closingprice)
VALUES ('labor', 'Labor', 200),
       ('agri', 'Agricultural products', 55),
       ('croil', 'Crude Oil', 100),
       ('metal', 'Metal', 120),
       ('groc', 'Grocery', 110),
       ('cloth', 'Clothing', 100),
       ('fuel', 'Fuel', 130),
       ('chem', 'Chemicals', 100),
       ('elect', 'Electronics', 300)
ON CONFLICT (ticker) DO NOTHING;