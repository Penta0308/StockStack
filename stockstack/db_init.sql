CREATE SCHEMA stsk_auth AUTHORIZATION stockstack;

CREATE TABLE stsk_auth.apiusers (uid SERIAL PRIMARY KEY, privilege BIT(64) DEFAULT 0::BIT(64));
CREATE TABLE stsk_auth.apikeys (uid INT REFERENCES stsk_auth.apiusers (uid), apikey CHAR(86) PRIMARY KEY, ratelimit INT DEFAULT -1);

--DROP TABLE stsk_auth.apiusers CASCADE;
--DROP TABLE stsk_auth.apikeys;

UPDATE stsk_auth.apiusers SET privilege = 0::BIT(64) WHERE uid = 0;

SELECT * FROM stsk_auth.apiusers;