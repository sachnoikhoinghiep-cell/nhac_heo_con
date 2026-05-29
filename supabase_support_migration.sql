-- ============================================================
-- Support Tickets Migration
-- Chạy trong Supabase SQL Editor
-- ============================================================

CREATE TABLE IF NOT EXISTS support_tickets (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      TEXT        NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    payment_id   UUID        REFERENCES payment_requests(id),
    issue_type   TEXT        NOT NULL,
    description  TEXT        NOT NULL,
    bank_details TEXT,
    admin_note   TEXT,
    status       TEXT        NOT NULL DEFAULT 'pending'
                             CHECK (status IN ('pending', 'resolved', 'rejected')),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tickets_user   ON support_tickets(user_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_created ON support_tickets(created_at);

-- RLS: user chỉ đọc/ghi ticket của chính mình; service_role bypass toàn bộ
ALTER TABLE support_tickets ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_own_tickets_select"
    ON support_tickets FOR SELECT
    USING (user_id = auth.uid()::text);

CREATE POLICY "user_own_tickets_insert"
    ON support_tickets FOR INSERT
    WITH CHECK (user_id = auth.uid()::text);
