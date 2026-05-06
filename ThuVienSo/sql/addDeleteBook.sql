use digital_library;
ALTER TABLE books
ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT 0;
