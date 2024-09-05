-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Subscriptions table
CREATE TABLE subscriptions (
    subscription_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    plan_name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    start_date DATE NOT NULL,
    end_date DATE,
    tts_monthly_limit INTEGER,
    stt_monthly_limit INTEGER
);

-- Payments table
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    subscription_id INTEGER REFERENCES subscriptions(subscription_id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50)
);

-- TTS activity table
CREATE TABLE tts_activity (
    tts_activity_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    character_count INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- STT activity table
CREATE TABLE stt_activity (
    stt_activity_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    duration_seconds INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
