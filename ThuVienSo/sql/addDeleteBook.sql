use digital_library;
ALTER TABLE books
ADD COLUMN is_deleted BOOLEAN DEFAULT 0;