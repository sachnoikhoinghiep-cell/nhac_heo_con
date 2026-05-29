-- ============================================================
-- BYOK (Bring Your Own Key) Migration
-- Chạy trong Supabase SQL Editor
-- ============================================================

-- 1. Thêm cột service_type vào subscription_plans
--    bundled = Hệ thống cung cấp API key + trừ Xu
--    byok    = Khách dùng key riêng + không giới hạn lượt
ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS service_type TEXT NOT NULL DEFAULT 'bundled'
        CHECK (service_type IN ('bundled', 'byok'));

-- 2. Đánh dấu các gói hiện tại là 'bundled'
UPDATE subscription_plans
SET service_type = 'bundled'
WHERE name IN ('Trải Nghiệm', 'Content Creator', 'Agency / VIP', 'Nạp Thêm');

-- 3. Thêm gói Tự Túc (BYOK)
INSERT INTO subscription_plans
    (name, price_vnd, duration_days, initial_credits, plan_type, service_type, description, is_active)
VALUES
    ('Gói Tự Túc', 149000, 30, 0, 'subscription', 'byok',
     'Unlimited — dùng API Key cá nhân, không giới hạn số lần tạo', TRUE)
ON CONFLICT (name) DO UPDATE SET
    price_vnd    = EXCLUDED.price_vnd,
    service_type = EXCLUDED.service_type,
    description  = EXCLUDED.description,
    is_active    = EXCLUDED.is_active;

-- 4. Tái tạo view active_subscriptions — thêm service_type
DROP VIEW IF EXISTS active_subscriptions;
CREATE VIEW active_subscriptions AS
SELECT
    us.id,
    us.user_id,
    us.plan_id,
    us.status,
    us.started_at,
    us.expires_at,
    us.paid_at,
    us.payment_provider,
    us.payment_reference,
    us.credits,
    sp.name          AS plan_name,
    sp.duration_days,
    sp.price_vnd,
    sp.initial_credits,
    sp.service_type
FROM user_subscriptions us
JOIN subscription_plans sp ON sp.id = us.plan_id
WHERE us.status = 'active'
  AND us.expires_at > now();
