-- ============================================================
-- Migration: 72h project auto-cleanup via pg_cron
-- Chạy trong Supabase SQL Editor (cần quyền superuser / Dashboard)
-- ============================================================

-- Bước 1: Bật extension pg_cron (chỉ cần chạy 1 lần)
create extension if not exists pg_cron;

-- Bước 2: Lên lịch xóa project hết hạn mỗi giờ
--   - Xóa tất cả project có expires_at != null và đã quá hạn
--   - Cascade sẽ tự xóa project_tracks, track_audio, project_images liên quan
select cron.schedule(
    'delete-expired-projects',          -- tên job (unique)
    '0 * * * *',                        -- mỗi giờ vào phút 0
    $$
    delete from projects
    where expires_at is not null
      and expires_at < now();
    $$
);

-- Kiểm tra job đã được đăng ký chưa:
-- select * from cron.job where jobname = 'delete-expired-projects';

-- Hủy job nếu cần:
-- select cron.unschedule('delete-expired-projects');

-- ============================================================
-- Lưu ý:
--   - Supabase Free tier: pg_cron có sẵn, không cần cài thêm
--   - Job chạy trong database timezone (UTC)
--   - expires_at được set = now() + 72h khi tạo project
--   - Kết hợp với include_expired=False trong get_projects() để
--     không hiện project đã hết hạn ngay khi UI load (trước khi cron xóa)
-- ============================================================
