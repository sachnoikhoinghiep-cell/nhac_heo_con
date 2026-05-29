-- ============================================================
-- Coins System Update Migration
-- Chạy trong Supabase SQL Editor (sau supabase_credits_migration.sql)
-- ============================================================

-- 1. Cập nhật giá và số coin cho các gói mới
UPDATE subscription_plans SET
    price_vnd       = 49000,
    initial_credits = 100,
    description     = '100 Xu — tạo ~10 MV hoàn chỉnh (Script+Ảnh+Nhạc)'
WHERE name = 'Trải Nghiệm';

UPDATE subscription_plans SET
    price_vnd       = 499000,
    initial_credits = 1200,
    description     = '1.200 Xu — duy trì 2-3 MV/ngày suốt tháng'
WHERE name = 'Content Creator';

UPDATE subscription_plans SET
    price_vnd       = 999000,
    initial_credits = 3000,
    description     = '3.000 Xu — quản lý đa kênh không giới hạn'
WHERE name = 'Agency / VIP';

UPDATE subscription_plans SET
    price_vnd       = 100000,
    initial_credits = 300,
    description     = 'Cộng ngay 300 Xu vào gói đang dùng'
WHERE name = 'Nạp Thêm';

-- 2. Bảng quy đổi Xu theo tác vụ (tài liệu tham khảo)
-- Sinh kịch bản / lời nhạc (LLM call)  : 1 Xu
-- Tạo / đổi ảnh thumbnail (fal.ai)      : 1 Xu
-- Render nhạc Suno                       : 5 Xu
-- → 1 MV hoàn chỉnh = 7 Xu
-- → 100 Xu  ≈ 14 MV    | 1.200 Xu ≈ 171 MV  | 3.000 Xu ≈ 428 MV
