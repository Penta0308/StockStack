CREATE SCHEMA {{ schemaname }};
SET search_path TO {{ schemaname }};

CREATE TABLE apiusers (uid SERIAL PRIMARY KEY, trader TEXT DEFAULT NULL, privilege BIT(64) DEFAULT 0::BIT(64) NOT NULL);
CREATE TABLE apikeys (uid INT REFERENCES apiusers (uid), apikey CHAR(86) PRIMARY KEY, ratelimit INT DEFAULT -1 NOT NULL);

CREATE TABLE stocks (ticker TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL, totalamount INT DEFAULT 0 NOT NULL, parvalue INT DEFAULT 5000, closingprice INT DEFAULT 5000);

CREATE TABLE traders (tid SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL);

CREATE TABLE stockowns(tid INT REFERENCES traders (tid), ticker TEXT REFERENCES stocks (ticker), amount INT DEFAULT 0 NOT NULL);