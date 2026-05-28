-- ============================================================
-- SePay Integration Migration
-- Chạy trong Supabase SQL Editor
-- ============================================================

-- 1. Thêm cột giá VNĐ vào subscription_plans
alter table subscription_plans
    add column if not exists price_vnd integer not null default 0;

update subscription_plans set price_vnd =    19000 where name = 'Ngày';
update subscription_plans set price_vnd =    69000 where name = 'Tuần';
update subscription_plans set price_vnd =   199000 where name = 'Tháng';
update subscription_plans set price_vnd = 1490000 where name = 'Năm';

-- Cập nhật mô tả gói theo chiến lược mới
alter table subscription_plans
    add column if not exists description text;

update subscription_plans set description = 'Thử nghiệm hệ thống, xem luồng tự động hóa'   where name = 'Ngày';
update subscription_plans set description = 'Đẩy nhanh tiến độ 1–2 kênh YouTube trong tuần' where name = 'Tuần';
update subscription_plans set description = 'Công cụ làm việc chính cho content creator'     where name = 'Tháng';
update subscription_plans set description = 'Ưu tiên cập nhật dòng nhạc & kịch bản mới'     where name = 'Năm';

-- 2. Bảng payment_requests — theo dõi từng giao dịch SePay
create table if not exists payment_requests (
    id                  uuid        primary key default gen_random_uuid(),
    user_id             text        not null references profiles(id) on delete cascade,
    plan_id             int         not null references subscription_plans(id),
    payment_code        text        not null unique,   -- SONIC + 8 ký tự, dùng làm nội dung CK
    amount_vnd          integer     not null,
    status              text        not null default 'pending'
                            check (status in ('pending','completed','expired','failed')),
    sepay_transaction_id text,
    sepay_reference      text,
    created_at          timestamptz not null default now(),
    expires_at          timestamptz not null default (now() + interval '30 minutes'),
    completed_at        timestamptz
);

create index if not exists idx_pay_req_code   on payment_requests(payment_code);
create index if not exists idx_pay_req_user   on payment_requests(user_id);
create index if not exists idx_pay_req_status on payment_requests(status);

-- 3. RLS
alter table payment_requests enable row level security;

-- User chỉ xem request của mình; service_role bypass toàn bộ
create policy "user_own_payments"
    on payment_requests for select
    using (user_id = auth.uid()::text);

-- 4. Auto-expire: đánh dấu pending quá hạn thành expired
--    Gọi thủ công hoặc lên lịch qua pg_cron:
-- select cron.schedule('expire-payments','*/5 * * * *',
--   $$ update payment_requests
--      set status='expired'
--      where status='pending' and expires_at < now() $$);
