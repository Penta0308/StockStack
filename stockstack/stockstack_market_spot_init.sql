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
    cid     INT REFERENCES world.companies (cid),
    ticker  TEXT REFERENCES stocks (ticker),
    amount  INT   DEFAULT 0 NOT NULL,
    amprice FLOAT DEFAULT 0 NOT NULL,
    CONSTRAINT stockowns_cid_ticker_constraint UNIQUE (cid, ticker)
);

CREATE TABLE IF NOT EXISTS stockorders
(
    ots       INT PRIMARY KEY,
    cid       INT REFERENCES world.companies (cid),
    ticker    TEXT REFERENCES stocks (ticker),
    direction INT2 NOT NULL,
    iamount   INT  NOT NULL,
    pamount   INT  NOT NULL,
    price     INT
);
CREATE TABLE IF NOT EXISTS stockorderspending
(
    ots       SERIAL PRIMARY KEY,
    cid       INT REFERENCES world.companies (cid),
    ticker    TEXT REFERENCES stocks (ticker),
    direction INT2 NOT NULL,
    iamount   INT  NOT NULL,
    pamount   INT  NOT NULL DEFAULT 0,
    price     INT,
    CONSTRAINT stockorderspending_cid_ticker_constraint UNIQUE (cid, ticker)
);

CREATE TABLE IF NOT EXISTS stockordershistory
(
    ots       INT PRIMARY KEY,
    cid       INT  NOT NULL,
    ticker    TEXT NOT NULL,
    direction INT2 NOT NULL,
    iamount   INT  NOT NULL,
    pamount   INT  NOT NULL,
    price     INT
);
SELECT addons.create_hypertable('stockordershistory', 'ots', chunk_time_interval => 4096, if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS stockpricechart
(
    tickn   INT  NOT NULL,
    ticker  TEXT NOT NULL,
    mprice  INT,
    hprice  INT,
    lprice  INT,
    tamount INT
);
SELECT addons.create_hypertable('stockpricechart', 'tickn', chunk_time_interval => 600, if_not_exists => TRUE);

INSERT INTO stocks (ticker, name, closingprice, parvalue)
VALUES ('labor', 'Labor', 200, 200),
       ('agri', 'Agricultural products', 55, default),
       ('croil', 'Crude Oil', 100, default),
       ('metal', 'Metal', 120, default),
       ('groc', 'Grocery', 110, default),
       ('cloth', 'Clothing', 100, default),
       ('fuel', 'Fuel', 130, default),
       ('chem', 'Chemicals', 100, default),
       ('elect', 'Electronics', 300, default)
ON CONFLICT (ticker) DO NOTHING;
