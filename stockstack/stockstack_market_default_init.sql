CREATE TABLE IF NOT EXISTS lconfig
(
    key   TEXT PRIMARY KEY,
    value TEXT
);

INSERT INTO lconfig (key, value)
VALUES ('market_variancerate_float', '0.3'),
       ('market_pricestepsize_fe', $$1 /1000 5 /5000 10 /10000 50 /50000 100 /100000 500 /500000 1000$$)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE IF NOT EXISTS stocks
(
    ticker       TEXT PRIMARY KEY,
    name         TEXT UNIQUE      NOT NULL,
    cid          INT REFERENCES world.companies (cid),
    parvalue     INT DEFAULT 5000 NOT NULL,
    closingprice INT DEFAULT 5000 NOT NULL,
    lastprice    INT DEFAULT 5000 NOT NULL
);

CREATE TABLE IF NOT EXISTS stockowns
(
    cid      INT REFERENCES world.companies (cid),
    ticker   TEXT REFERENCES stocks (ticker),
    amount   INT DEFAULT 0 NOT NULL,
    totprice INT DEFAULT 0 NOT NULL,
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