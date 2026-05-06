USE digital_library;
-- Nếu chạy trên PythonAnywhere thì đổi thành:
-- USE `namvfg$digital_library`;

ALTER TABLE borrow_request_items
    ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;

ALTER TABLE borrow_record_items
    ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;

START TRANSACTION;

-- =========================
-- CONFIG: đổi theo tài khoản cần sửa
-- =========================
SET @target_username = 'ngocanh';
SET @preferred_branch_name = 'Chi nhánh Võ Văn Tần';

SET @user_id = NULL;
SET @branch_id = NULL;

-- Lấy user_id theo username, có xử lý lỗi collation
SELECT @user_id := id
FROM users
WHERE username COLLATE utf8mb4_unicode_ci = @target_username COLLATE utf8mb4_unicode_ci
LIMIT 1;

-- Lấy branch_id theo tên chi nhánh, có xử lý lỗi collation
SELECT @branch_id := id
FROM branches
WHERE name COLLATE utf8mb4_unicode_ci = @preferred_branch_name COLLATE utf8mb4_unicode_ci
LIMIT 1;

-- Kiểm tra biến trước khi sửa
SELECT 
    @target_username AS target_username,
    @user_id AS user_id,
    @preferred_branch_name AS preferred_branch_name,
    @branch_id AS branch_id;

-- =========================
-- 1. Cập nhật trạng thái trễ hạn nếu có phiếu quá hạn
-- =========================
UPDATE borrow_records
SET status = 'overdue'
WHERE user_id = @user_id
  AND status = 'borrowing'
  AND due_date < NOW()
  AND @user_id IS NOT NULL;

-- =========================
-- 2. Xóa request không hợp lệ của user
-- - Xóa pending request khi user đang bị overdue / dữ liệu test cũ
-- - Xóa approved request nhưng không có sách bên trong
-- =========================
DROP TEMPORARY TABLE IF EXISTS tmp_requests_to_delete;

CREATE TEMPORARY TABLE tmp_requests_to_delete AS
SELECT br.id AS request_id
FROM borrow_requests br
LEFT JOIN borrow_request_items bri ON bri.borrow_request_id = br.id
WHERE br.user_id = @user_id
  AND @user_id IS NOT NULL
GROUP BY br.id, br.status
HAVING br.status = 'pending'
   OR (br.status = 'approved' AND COUNT(bri.id) = 0);

-- Cắt liên kết từ borrow_records tới request bẩn trước khi xóa
-- Nếu borrow_request_id không tồn tại hoặc không cho NULL thì báo mình sửa bản khác.
UPDATE borrow_records br
JOIN tmp_requests_to_delete t ON t.request_id = br.borrow_request_id
SET br.borrow_request_id = NULL
WHERE br.user_id = @user_id
  AND @user_id IS NOT NULL;

-- Xóa item của các request cần xóa
DELETE bri
FROM borrow_request_items bri
JOIN tmp_requests_to_delete t ON t.request_id = bri.borrow_request_id;

-- Xóa request cần xóa
DELETE br
FROM borrow_requests br
JOIN tmp_requests_to_delete t ON t.request_id = br.id;

-- =========================
-- 3. Gán book_copy_id cho lịch sử mượn cũ bị thiếu chi nhánh
-- Ưu tiên gán theo chi nhánh đã chọn.
-- =========================
UPDATE borrow_record_items bri
JOIN borrow_records br ON br.id = bri.borrow_record_id
JOIN book_copies bc
    ON bc.book_id = bri.book_id
   AND bc.branch_id = @branch_id
SET bri.book_copy_id = bc.id
WHERE br.user_id = @user_id
  AND bri.book_copy_id IS NULL
  AND @user_id IS NOT NULL
  AND @branch_id IS NOT NULL;

-- =========================
-- 4. Fallback: nếu sách không có ở chi nhánh trên,
-- tự lấy book_copy đầu tiên của sách đó.
-- =========================
UPDATE borrow_record_items bri
JOIN borrow_records br ON br.id = bri.borrow_record_id
JOIN (
    SELECT book_id, MIN(id) AS first_book_copy_id
    FROM book_copies
    GROUP BY book_id
) fc ON fc.book_id = bri.book_id
SET bri.book_copy_id = fc.first_book_copy_id
WHERE br.user_id = @user_id
  AND bri.book_copy_id IS NULL
  AND @user_id IS NOT NULL;

COMMIT;

-- =========================
-- 5. Kiểm tra sau khi sửa
-- =========================

-- Kiểm tra còn request pending / approved bẩn không
SELECT 
    br.id,
    br.user_id,
    u.username,
    br.status,
    br.created_at,
    br.note
FROM borrow_requests br
JOIN users u ON u.id = br.user_id
WHERE br.user_id = @user_id
ORDER BY br.id;

-- Kiểm tra lịch sử mượn đã có chi nhánh chưa
SELECT 
    br.id AS borrow_record_id,
    u.username,
    br.status,
    br.borrow_date,
    br.due_date,
    b.title,
    bri.id AS item_id,
    bri.book_id,
    bri.book_copy_id,
    bc.branch_id,
    branches.name AS branch_name
FROM borrow_records br
JOIN users u ON u.id = br.user_id
JOIN borrow_record_items bri ON bri.borrow_record_id = br.id
JOIN books b ON b.id = bri.book_id
LEFT JOIN book_copies bc ON bc.id = bri.book_copy_id
LEFT JOIN branches ON branches.id = bc.branch_id
WHERE br.user_id = @user_id
ORDER BY br.id, bri.id;
