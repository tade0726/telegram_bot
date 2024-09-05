-- Insert mock users
INSERT INTO users (user_id, username, email) VALUES
(1, 'john_doe', 'john@example.com'),
(2, 'jane_smith', 'jane@example.com'),
(3, 'bob_johnson', 'bob@example.com');

-- Insert mock subscriptions
INSERT INTO subscriptions (subscription_id, user_id, plan_name, is_active, start_date, end_date, tts_monthly_limit, stt_monthly_limit) VALUES
(1, 1, 'Basic', TRUE, '2024-01-01', '2024-12-31', 10000, 3600),
(2, 2, 'Premium', TRUE, '2024-01-15', '2025-01-14', 50000, 18000),
(3, 3, 'Free', TRUE, '2024-02-01', NULL, 5000, 1800);

-- Insert mock payments
INSERT INTO payments (user_id, subscription_id, amount, payment_method) VALUES
(1, 1, 9.99, 'Credit Card'),
(2, 2, 19.99, 'PayPal'),
(2, 2, 19.99, 'PayPal');

-- Insert mock TTS activity
INSERT INTO tts_activity (user_id, character_count) VALUES
(1, 1500),
(1, 2000),
(2, 3000),
(2, 4000),
(2, 5000),
(3, 1000);

-- Insert mock STT activity
INSERT INTO stt_activity (user_id, duration_seconds) VALUES
(1, 300),
(1, 450),
(2, 600),
(2, 750),
(2, 900),
(3, 200);

-- Verify data insertion
SELECT 'users' AS table_name, COUNT(*) AS record_count FROM users
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'tts_activity', COUNT(*) FROM tts_activity
UNION ALL
SELECT 'stt_activity', COUNT(*) FROM stt_activity;