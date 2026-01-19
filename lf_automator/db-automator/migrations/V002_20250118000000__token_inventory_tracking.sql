-- Token Inventory Tracking Feature Migration
-- Creates new tables for member token registry, alert state, and count timestamps
-- Updates accessTokenPools table with status and priority columns

-- Create memberTokenRegistry table
CREATE TABLE IF NOT EXISTS lfautomator.memberTokenRegistry (
    registryUuid UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    memberUuid UUID NOT NULL UNIQUE,
    tokenNumber VARCHAR(50) NOT NULL,
    registeredAt TIMESTAMP NOT NULL DEFAULT NOW(),
    updatedAt TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_member_token_registry_registered 
ON lfautomator.memberTokenRegistry(registeredAt);

-- Create alertState table
CREATE TABLE IF NOT EXISTS lfautomator.alertState (
    alertUuid UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    alertType VARCHAR(50) NOT NULL,
    lastTriggered TIMESTAMP,
    isActive BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Create countTimestamps table
CREATE TABLE IF NOT EXISTS lfautomator.countTimestamps (
    timestampUuid UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    countType VARCHAR(50) NOT NULL UNIQUE,
    lastCountAt TIMESTAMP NOT NULL,
    executionStatus VARCHAR(20),
    tokensDistributed INT,
    metadata JSONB
);

-- Update accessTokenPools table with new columns
ALTER TABLE lfautomator.accessTokenPools 
ADD COLUMN IF NOT EXISTS poolStatus VARCHAR(20) DEFAULT 'active';

ALTER TABLE lfautomator.accessTokenPools 
ADD COLUMN IF NOT EXISTS poolPriority INT DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_token_pools_status_priority 
ON lfautomator.accessTokenPools(poolStatus, poolPriority);
