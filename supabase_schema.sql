-- ============================================================
-- nhacheocon — Supabase Schema (Firebase Auth hybrid)
-- profiles.id = Firebase UID (text), không phụ thuộc auth.users
-- Chạy toàn bộ file này trong Supabase SQL Editor
-- ============================================================

-- ENUM types
create type user_role           as enum ('admin', 'user');
create type subscription_status as enum ('active', 'expired', 'cancelled', 'pending');
create type payment_provider    as enum ('paypal', 'manual', 'free');
create type api_provider        as enum ('anthropic', 'google', 'suno', 'fal');
create type project_status      as enum ('generating', 'completed', 'failed');
create type track_status        as enum ('pending', 'processing', 'done', 'failed');
create extension if not exists pgcrypto;

-- ============================================================
-- 1. PROFILES
-- ============================================================
create table if not exists profiles (
    id          text primary key,                   -- Firebase UID
    email       text not null,
    full_name   text,
    avatar_url  text,
    role        user_role    not null default 'user',
    created_at  timestamptz  not null default now(),
    updated_at  timestamptz  not null default now()
);

create index if not exists idx_profiles_email on profiles(email);
create index if not exists idx_profiles_role  on profiles(role);

-- ============================================================
-- 2. SUBSCRIPTION PLANS
-- ============================================================
create table if not exists subscription_plans (
    id              serial primary key,
    name            text          not null unique,
    price_usd       numeric(10,2) not null,
    duration_days   int           not null,
    paypal_plan_id  text,
    is_active       boolean       not null default true,
    created_at      timestamptz   not null default now()
);

insert into subscription_plans (name, price_usd, duration_days, paypal_plan_id)
values
    ('Ngày',  0.99,   1,   'P-48U172572M537580PNICAPDY'),
    ('Tuần',  4.99,   7,   'P-12862804M08177324NICAPSI'),
    ('Tháng', 14.99,  30,  'P-5AV04190G6017082ENICAOVA'),
    ('Năm',   99.99,  365, 'P-055284903H354632FNICAN7I')
on conflict (name) do nothing;

-- ============================================================
-- 3. USER SUBSCRIPTIONS
-- ============================================================
create table if not exists user_subscriptions (
    id                  uuid         primary key default gen_random_uuid(),
    user_id             text         not null references profiles(id) on delete cascade,
    plan_id             int          not null references subscription_plans(id),
    status              subscription_status not null default 'pending',
    started_at          timestamptz,
    expires_at          timestamptz,
    paid_at             timestamptz,
    payment_provider    payment_provider    not null default 'paypal',
    payment_reference   text,
    created_at          timestamptz  not null default now()
);

create index if not exists idx_subs_user    on user_subscriptions(user_id);
create index if not exists idx_subs_status  on user_subscriptions(status);
create index if not exists idx_subs_expires on user_subscriptions(expires_at);

-- View: gói active hiện tại của từng user
create or replace view active_subscriptions as
select distinct on (user_id)
    us.id,
    us.user_id,
    us.status,
    us.started_at,
    us.expires_at,
    us.paid_at,
    us.payment_reference,
    sp.name           as plan_name,
    sp.duration_days,
    sp.price_usd
from user_subscriptions us
join subscription_plans sp on sp.id = us.plan_id
where us.status = 'active'
  and us.expires_at > now()
order by user_id, expires_at desc;

-- ============================================================
-- 4. USER API KEYS (mã hoá app-side bằng Fernet)
-- ============================================================
create table if not exists user_api_keys (
    id             uuid         primary key default gen_random_uuid(),
    user_id        text         not null references profiles(id) on delete cascade,
    provider       api_provider not null,
    encrypted_key  text         not null,
    created_at     timestamptz  not null default now(),
    updated_at     timestamptz  not null default now(),
    unique (user_id, provider)
);

create index if not exists idx_apikeys_user on user_api_keys(user_id);

-- ============================================================
-- 5. PROJECTS
-- ============================================================
create table if not exists projects (
    id              uuid          primary key default gen_random_uuid(),
    user_id         text          not null references profiles(id) on delete cascade,
    name            text          not null,
    topic           text,
    genre           text,
    language        text          default 'vi',
    num_tracks      smallint      not null default 1,
    create_mv       boolean       not null default false,
    status          project_status not null default 'generating',
    claude_result   jsonb,
    seo_metadata    jsonb,
    expires_at      timestamptz,
    created_at      timestamptz   not null default now(),
    updated_at      timestamptz   not null default now()
);

create index if not exists idx_projects_user    on projects(user_id);
create index if not exists idx_projects_created on projects(created_at desc);
create index if not exists idx_projects_expires on projects(expires_at) where expires_at is not null;

-- ============================================================
-- 6. PROJECT TRACKS
-- ============================================================
create table if not exists project_tracks (
    id             uuid         primary key default gen_random_uuid(),
    project_id     uuid         not null references projects(id) on delete cascade,
    track_number   smallint     not null,
    title          text,
    lyrics         text,
    style_tags     text,
    suno_task_id   text,
    status         track_status not null default 'pending',
    error_message  text,
    created_at     timestamptz  not null default now(),
    updated_at     timestamptz  not null default now(),
    unique (project_id, track_number)
);

create index if not exists idx_tracks_project on project_tracks(project_id);

-- ============================================================
-- 7. TRACK AUDIO
-- ============================================================
create table if not exists track_audio (
    id             uuid        primary key default gen_random_uuid(),
    track_id       uuid        not null references project_tracks(id) on delete cascade,
    version        char(1)     not null check (version in ('A','B')),
    suno_id        text,
    audio_url      text,
    stream_url     text,
    image_url      text,
    duration_secs  numeric(6,2),
    created_at     timestamptz not null default now(),
    unique (track_id, version)
);

-- ============================================================
-- 8. PROJECT IMAGES
-- ============================================================
create table if not exists project_images (
    id             uuid        primary key default gen_random_uuid(),
    project_id     uuid        not null references projects(id) on delete cascade,
    prompt         text        not null,
    image_url      text,
    aspect_ratio   text        not null default '16:9',
    resolution     text        not null default '1K',
    created_at     timestamptz not null default now()
);

create index if not exists idx_images_project on project_images(project_id);

-- ============================================================
-- 9. RLS (dùng service_role key từ app → bypass RLS)
--    RLS ở đây là safety net nếu dùng anon key hoặc Dashboard
-- ============================================================
alter table profiles            enable row level security;
alter table user_subscriptions  enable row level security;
alter table user_api_keys       enable row level security;
alter table projects            enable row level security;
alter table project_tracks      enable row level security;
alter table track_audio         enable row level security;
alter table project_images      enable row level security;

-- service_role bypass mặc định (Supabase tự xử lý)
-- Thêm policy cho anon/authenticated nếu cần Dashboard access

-- ============================================================
-- 10. AUTO-DELETE projects hết hạn
--     Kích hoạt trong Supabase > Database > Extensions > pg_cron
-- ============================================================
-- select cron.schedule(
--     'delete-expired-projects',
--     '0 * * * *',   -- mỗi giờ
--     $$ delete from projects where expires_at is not null and expires_at < now() $$
-- );
