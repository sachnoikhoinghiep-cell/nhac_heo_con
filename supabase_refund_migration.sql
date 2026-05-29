-- ============================================================
-- Refund Support Migration
-- Chạy trong Supabase SQL Editor sau supabase_sepay_migration.sql
-- ============================================================

-- 1. Thêm trạng thái 'refunded' vào payment_requests
--    (xóa check constraint cũ rồi tạo lại với đủ giá trị)
alter table payment_requests
    drop constraint if exists payment_requests_status_check;

alter table payment_requests
    add constraint payment_requests_status_check
    check (status in ('pending', 'completed', 'expired', 'failed', 'refunded'));

-- 2. Cột lý do hoàn tiền và thời điểm hoàn tiền
alter table payment_requests
    add column if not exists refund_reason text,
    add column if not exists refunded_at   timestamptz;
