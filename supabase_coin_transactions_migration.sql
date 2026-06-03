-- ============================================================
-- Migration: coin_transactions table
-- Chạy trong Supabase SQL Editor
-- ============================================================

create table if not exists coin_transactions (
    id          uuid        primary key default gen_random_uuid(),
    user_id     text        not null references profiles(id) on delete cascade,
    delta       int         not null,       -- âm = tiêu, dương = nạp/kích hoạt
    balance     int         not null,       -- số dư SAU giao dịch này
    action      text        not null,       -- 'suno' | 'image' | 'script' | 'activate' | 'topup'
    description text,
    created_at  timestamptz not null default now()
);

create index if not exists idx_coin_tx_user    on coin_transactions(user_id);
create index if not exists idx_coin_tx_created on coin_transactions(created_at desc);

alter table coin_transactions enable row level security;
