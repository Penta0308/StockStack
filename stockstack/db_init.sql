CREATE SCHEMA stsk_auth AUTHORIZATION stockstack;

CREATE TABLE stsk_auth.apiusers (uid SERIAL PRIMARY KEY, market VARCHAR DEFAULT NULL, privilege BIT(64) DEFAULT 0::BIT(64) NOT NULL);
CREATE TABLE stsk_auth.apikeys (uid INT REFERENCES stsk_auth.apiusers (uid), apikey CHAR(86) PRIMARY KEY, ratelimit INT DEFAULT -1 NOT NULL);
