CREATE SCHEMA IF NOT EXISTS discordbot;

CREATE TABLE IF NOT EXISTS discordbot.discorduser
(
    discorduid BIGINT PRIMARY KEY,
    cid        INT NOT NULL UNIQUE
);