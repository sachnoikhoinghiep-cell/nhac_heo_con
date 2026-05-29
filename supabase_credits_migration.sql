-- ============================================================
-- Credits-Based Subscription Migration
-- Chạy trong Supabase SQL Editor
-- ============================================================

-- 1. Thêm cột initial_credits và plan_type vào subscription_plans
ALTER TABLE subscription_plans
    ADD COLUMN IF NOT EXISTS initial_credits INT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS plan_type TEXT NOT NULL DEFAULT 'subscription'
        CHECK (plan_type IN ('subscription', 'topup'));

-- 2. Thêm cột credits vào user_subscriptions
ALTER TABLE user_subscriptions
    ADD COLUMN IF NOT EXISTS credits INT NOT NULL DEFAULT 0;

-- 3. Bảo toàn quyền lợi người dùng cũ đang active
--    (gán 100 lượt để không bị mất quyền truy cập ngay lập tức)
UPDATE user_subscriptions
SET credits = 100
WHERE status = 'active'
  AND expires_at > now()
  AND credits = 0;

-- 4. Vô hiệu hóa các gói cũ (giữ dữ liệu lịch sử)
UPDATE subscription_plans
SET is_active = FALSE
WHERE name IN ('Ngày', 'Tuần', 'Tháng', 'Năm');

-- 5. Thêm / cập nhật các gói mới
INSERT INTO subscription_plans
    (name, price_usd, price_vnd, duration_days, initial_credits, plan_type, description, is_active)
VALUES
    ('Trải Nghiệm',     0,   49000,  1,  10,  'subscription', 'Thử nghiệm toàn bộ tính năng trong 24 giờ',          TRUE),
    ('Content Creator', 0,  399000, 30, 100, 'subscription', '100 lượt tạo MV — đủ duy trì 1 kênh YouTube/tháng',   TRUE),
    ('Agency / VIP',    0,  899000, 30, 300, 'subscription', '300 lượt + dòng nhạc ngách đặc biệt',                  TRUE),
    ('Nạp Thêm',        0,  100000,  0,  30,  'topup',        'Cộng thêm 30 lượt vào gói đang dùng',                 TRUE)
ON CONFLICT (name) DO UPDATE SET
    price_vnd       = EXCLUDED.price_vnd,
    duration_days   = EXCLUDED.duration_days,
    initial_credits = EXCLUDED.initial_credits,
    plan_type       = EXCLUDED.plan_type,
    description     = EXCLUDED.description,
    is_active       = EXCLUDED.is_active;

-- 6. Tái tạo view active_subscriptions — thêm cột credits
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
    sp.initial_credits
FROM user_subscriptions us
JOIN subscription_plans sp ON sp.id = us.plan_id
WHERE us.status = 'active'
  AND us.expires_at > now();
