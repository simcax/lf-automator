CREATE SCHEMA IF NOT EXISTS lfautomator;

CREATE TABLE IF NOT EXISTS lfautomator.accessTokenPools (
    poolUuid UUID NOT NULL PRIMARY KEY,
    poolDate DATE NOT NULL DEFAULT CURRENT_DATE,
    startCount SMALLINT NOT NULL,
    currentCount SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS lfautomator.accessTokenPoolsHistory(
    historyUuid UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    poolUuid UUID REFERENCES lfautomator.accessTokenPools(poolUuid),
    changeDate TIMESTAMP NOT NULL DEFAULT NOW(),
    accessTokenCount SMALLINT NOT NULL
);

