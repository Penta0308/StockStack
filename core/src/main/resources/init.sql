CREATE SCHEMA stockstack;

SET search_path TO 'stockstack';

CREATE TABLE t_user (
    userid serial PRIMARY KEY,
    username varchar NOT NULL,
    usertype int NOT NULL,
    usermoney bigint NOT NULL DEFAULT 0
);

CREATE TABLE t_asset (
    assetid serial PRIMARY KEY,
    assettype int NOT NULL,
    assetamount bigint NOT NULL DEFAULT 0
);

CREATE TABLE t_userasset (
    userid int NOT NULL REFERENCES t_user(userid),
    assetid int NOT NULL REFERENCES t_asset(assetid),
    assetamount bigint NOT NULL,
    assetinitialvalue bigint NOT NULL,
    PRIMARY KEY (userid, assetid)
);

CREATE TABLE t_logindiscord (
    userid int NOT NULL REFERENCES t_user(userid),
    discordid bigint PRIMARY KEY
);