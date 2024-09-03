-- Create Users table
CREATE TABLE Users (
    id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_premier BOOLEAN NOT NULL DEFAULT FALSE,
);

-- Create UserBehaviors table
CREATE TABLE UserBehaviors (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES Users(id),
    function_type TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create UserLimits table
CREATE TABLE UserLimits (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES Users(id),
    total_tokens_limit INTEGER NOT NULL,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    reset_date DATE NOT NULL
);

-- Create enum type for function_type
CREATE TYPE function_type AS ENUM ('text_to_audio', 'audio_to_text');

-- Alter UserBehaviors table to use the new enum type
ALTER TABLE UserBehaviors ALTER COLUMN function_type TYPE function_type USING function_type::function_type;