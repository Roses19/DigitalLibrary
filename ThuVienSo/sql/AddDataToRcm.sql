USE digital_library;

SET NAMES utf8mb4;


ALTER TABLE borrow_request_items
    ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;

ALTER TABLE borrow_record_items
    ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;


INSERT INTO roles (name, description)
SELECT 'Độc giả', 'Người dùng mượn và tìm kiếm sách'
WHERE NOT EXISTS (
    SELECT 1 FROM roles WHERE LOWER(name) IN ('độc giả', 'doc gia', 'reader')
);

SET @reader_role_id := (
    SELECT id FROM roles
    WHERE LOWER(name) IN ('độc giả', 'doc gia', 'reader')
    ORDER BY id
    LIMIT 1
);

INSERT INTO users (role_id, full_name, email, username, password_hash, phone, status, created_at)
SELECT @reader_role_id, 'Nguyễn Thị Ánh Hồng', '2251052039hong@ou.edu.vn', 'roses19',
       'pbkdf2:sha256:600000$demo$roses19', '0327761048', 'active', '2026-04-26 08:00:00'
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE username = 'roses19'
);

SET @roses_id := (SELECT id FROM users WHERE username = 'roses19' LIMIT 1);
SET @admin_id := (
    SELECT id FROM users
    WHERE username IN ('admin', 'maint')
    ORDER BY id
    LIMIT 1
);

-- ---------------------------------------------------------
-- Danh mục, NXB, tác giả bổ sung
-- ---------------------------------------------------------
INSERT INTO categories (name, description, created_at)
SELECT 'Khoa học dữ liệu', 'Dữ liệu, AI, khai phá tri thức', '2026-04-26 08:10:00'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Khoa học dữ liệu');

INSERT INTO categories (name, description, created_at)
SELECT 'Tâm lý học ứng dụng', 'Hành vi, thói quen và phát triển bản thân', '2026-04-26 08:11:00'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Tâm lý học ứng dụng');

INSERT INTO categories (name, description, created_at)
SELECT 'Văn học hiện đại', 'Tiểu thuyết, truyện dài hiện đại', '2026-04-26 08:12:00'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Văn học hiện đại');

INSERT INTO publishers (name, address, phone, email, created_at)
SELECT 'NXB Công nghệ tri thức', 'TP. Hồ Chí Minh', '0283000001', 'contact@trithuc.vn', '2026-04-26 08:15:00'
WHERE NOT EXISTS (SELECT 1 FROM publishers WHERE name = 'NXB Công nghệ tri thức');

INSERT INTO publishers (name, address, phone, email, created_at)
SELECT 'NXB Tri Thức Trẻ', 'Hà Nội', '0243000002', 'info@trithuctre.vn', '2026-04-26 08:16:00'
WHERE NOT EXISTS (SELECT 1 FROM publishers WHERE name = 'NXB Tri Thức Trẻ');

INSERT INTO authors (name, biography, created_at)
SELECT 'Andrew Ng', 'Tác giả các tài liệu nhập môn AI và machine learning.', '2026-04-26 08:20:00'
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE name = 'Andrew Ng');

INSERT INTO authors (name, biography, created_at)
SELECT 'James Clear', 'Tác giả viết về thói quen và thay đổi hành vi.', '2026-04-26 08:21:00'
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE name = 'James Clear');

INSERT INTO authors (name, biography, created_at)
SELECT 'Nguyễn Nhật Ánh', 'Nhà văn Việt Nam được độc giả trẻ yêu thích.', '2026-04-26 08:22:00'
WHERE NOT EXISTS (SELECT 1 FROM authors WHERE name = 'Nguyễn Nhật Ánh');

-- ---------------------------------------------------------
-- Chi nhánh
-- ---------------------------------------------------------
INSERT INTO branches (name, address, phone, created_at)
SELECT 'Chi nhánh Võ Văn Tần', 'Quận 3', '0283999003', '2026-04-26 08:28:00'
WHERE NOT EXISTS (SELECT 1 FROM branches WHERE name = 'Chi nhánh Võ Văn Tần');

INSERT INTO branches (name, address, phone, created_at)
SELECT 'Chi nhánh Hiệp Phước', 'Nhà Bè', '0283999004', '2026-04-26 08:29:00'
WHERE NOT EXISTS (SELECT 1 FROM branches WHERE name = 'Chi nhánh Hiệp Phước');

INSERT INTO branches (name, address, phone, created_at)
SELECT 'Chi nhánh Nguyễn Văn Bảo', 'Gò Vấp', '0283999001', '2026-04-26 08:30:00'
WHERE NOT EXISTS (SELECT 1 FROM branches WHERE name = 'Chi nhánh Nguyễn Văn Bảo');

INSERT INTO branches (name, address, phone, created_at)
SELECT 'Chi nhánh Quang Trung', 'Quận 12', '0283999002', '2026-04-26 08:31:00'
WHERE NOT EXISTS (SELECT 1 FROM branches WHERE name = 'Chi nhánh Quang Trung');

SET @cat_data := (SELECT id FROM categories WHERE name = 'Khoa học dữ liệu' LIMIT 1);
SET @cat_psych := (SELECT id FROM categories WHERE name = 'Tâm lý học ứng dụng' LIMIT 1);
SET @cat_lit := (SELECT id FROM categories WHERE name = 'Văn học hiện đại' LIMIT 1);
SET @pub_tech := (SELECT id FROM publishers WHERE name = 'NXB Công nghệ tri thức' LIMIT 1);
SET @pub_young := (SELECT id FROM publishers WHERE name = 'NXB Tri Thức Trẻ' LIMIT 1);
SET @author_ai := (SELECT id FROM authors WHERE name = 'Andrew Ng' LIMIT 1);
SET @author_habit := (SELECT id FROM authors WHERE name = 'James Clear' LIMIT 1);
SET @author_nna := (SELECT id FROM authors WHERE name = 'Nguyễn Nhật Ánh' LIMIT 1);

-- ---------------------------------------------------------
-- Sách bổ sung cho recommendation / semantic search
-- ---------------------------------------------------------
INSERT INTO books (category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, status, created_by, created_at)
SELECT @cat_data, @pub_tech, 'Nhập môn Học máy cho thư viện số', 'RCM-ML-001',
       'Machine learning cơ bản, hệ gợi ý sách, phân cụm độc giả và dự đoán nhu cầu mượn.',
       '/static/resources/books/ml-library.jpg', 2024, 'Tiếng Việt', 312, 'available', @admin_id, '2026-04-26 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM books WHERE isbn = 'RCM-ML-001');

INSERT INTO books (category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, status, created_by, created_at)
SELECT @cat_data, @pub_tech, 'Tìm kiếm ngữ nghĩa với Python', 'RCM-SEM-002',
       'Xây dựng semantic search, embedding văn bản, truy vấn gần nghĩa và xếp hạng kết quả.',
       '/static/resources/books/semantic-python.jpg', 2025, 'Tiếng Việt', 286, 'available', @admin_id, '2026-04-26 09:05:00'
WHERE NOT EXISTS (SELECT 1 FROM books WHERE isbn = 'RCM-SEM-002');

INSERT INTO books (category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, status, created_by, created_at)
SELECT @cat_psych, @pub_young, 'Thói quen đọc sách hiệu quả', 'RCM-HABIT-003',
       'Cách hình thành thói quen đọc, ghi chú và duy trì động lực học tập mỗi ngày.',
       '/static/resources/books/reading-habit.jpg', 2023, 'Tiếng Việt', 220, 'available', @admin_id, '2026-04-26 09:10:00'
WHERE NOT EXISTS (SELECT 1 FROM books WHERE isbn = 'RCM-HABIT-003');

INSERT INTO books (category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, status, created_by, created_at)
SELECT @cat_lit, @pub_young, 'Mùa hè trong mắt biếc', 'RCM-LIT-004',
       'Truyện dài nhẹ nhàng về tuổi trẻ, ký ức và những rung động đầu đời.',
       '/static/resources/books/mua-he-mat-biec.jpg', 2022, 'Tiếng Việt', 198, 'available', @admin_id, '2026-04-26 09:15:00'
WHERE NOT EXISTS (SELECT 1 FROM books WHERE isbn = 'RCM-LIT-004');

INSERT INTO books (category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, status, created_by, created_at)
SELECT @cat_data, @pub_tech, 'Phân tích dữ liệu mượn sách', 'RCM-DATA-005',
       'Phân tích hành vi mượn sách, xu hướng theo thời gian và dự báo tồn kho thư viện.',
       '/static/resources/books/borrow-analytics.jpg', 2025, 'Tiếng Việt', 340, 'available', @admin_id, '2026-04-27 09:00:00'
WHERE NOT EXISTS (SELECT 1 FROM books WHERE isbn = 'RCM-DATA-005');

SET @book_ml := (SELECT id FROM books WHERE isbn = 'RCM-ML-001' LIMIT 1);
SET @book_sem := (SELECT id FROM books WHERE isbn = 'RCM-SEM-002' LIMIT 1);
SET @book_habit := (SELECT id FROM books WHERE isbn = 'RCM-HABIT-003' LIMIT 1);
SET @book_lit := (SELECT id FROM books WHERE isbn = 'RCM-LIT-004' LIMIT 1);
SET @book_data := (SELECT id FROM books WHERE isbn = 'RCM-DATA-005' LIMIT 1);

INSERT IGNORE INTO book_authors (book_id, author_id) VALUES
(@book_ml, @author_ai),
(@book_sem, @author_ai),
(@book_habit, @author_habit),
(@book_lit, @author_nna),
(@book_data, @author_ai);

-- ---------------------------------------------------------
-- Book copies theo nhiều chi nhánh
-- ---------------------------------------------------------
SET @branch_vvt := (SELECT id FROM branches WHERE name = 'Chi nhánh Võ Văn Tần' LIMIT 1);
SET @branch_hp := (SELECT id FROM branches WHERE name = 'Chi nhánh Hiệp Phước' LIMIT 1);
SET @branch_nvb := (SELECT id FROM branches WHERE name = 'Chi nhánh Nguyễn Văn Bảo' LIMIT 1);
SET @branch_qt := (SELECT id FROM branches WHERE name = 'Chi nhánh Quang Trung' LIMIT 1);

INSERT IGNORE INTO book_copies (book_id, branch_id, shelf_location, total_quantity, available_quantity) VALUES
(@book_ml, @branch_vvt, 'AI-01', 6, 4),
(@book_ml, @branch_hp, 'AI-02', 4, 3),
(@book_sem, @branch_vvt, 'PY-SEM-01', 5, 4),
(@book_sem, @branch_nvb, 'PY-SEM-02', 3, 2),
(@book_habit, @branch_hp, 'SK-01', 6, 5),
(@book_habit, @branch_qt, 'SK-02', 4, 4),
(@book_lit, @branch_vvt, 'VH-11', 5, 3),
(@book_lit, @branch_hp, 'VH-12', 5, 4),
(@book_lit, @branch_nvb, 'VH-13', 2, 2),
(@book_data, @branch_vvt, 'DATA-01', 6, 5),
(@book_data, @branch_qt, 'DATA-02', 4, 3);

SET @copy_ml_vvt := (SELECT id FROM book_copies WHERE book_id = @book_ml AND branch_id = @branch_vvt LIMIT 1);
SET @copy_sem_vvt := (SELECT id FROM book_copies WHERE book_id = @book_sem AND branch_id = @branch_vvt LIMIT 1);
SET @copy_habit_hp := (SELECT id FROM book_copies WHERE book_id = @book_habit AND branch_id = @branch_hp LIMIT 1);
SET @copy_lit_hp := (SELECT id FROM book_copies WHERE book_id = @book_lit AND branch_id = @branch_hp LIMIT 1);
SET @copy_data_qt := (SELECT id FROM book_copies WHERE book_id = @book_data AND branch_id = @branch_qt LIMIT 1);

-- ---------------------------------------------------------
-- Lịch sử xem và tìm kiếm cho semantic search
-- ---------------------------------------------------------
INSERT INTO search_histories (user_id, keyword, search_type, created_at) VALUES
(@roses_id, 'sách giống Mắt Biếc về tuổi trẻ và ký ức', 'semantic', '2026-04-26 10:05:00'),
(@roses_id, 'machine learning gợi ý sách thư viện', 'semantic', '2026-04-27 09:45:00'),
(@roses_id, 'python tìm kiếm ngữ nghĩa embedding', 'semantic', '2026-05-01 08:30:00'),
(@roses_id, 'phân tích dữ liệu mượn sách', 'keyword', '2026-05-02 14:20:00'),
(@roses_id, 'thói quen đọc sách hiệu quả', 'semantic', '2026-05-02 19:10:00');

INSERT INTO book_views (user_id, book_id, viewed_at) VALUES
(@roses_id, @book_lit, '2026-04-26 10:10:00'),
(@roses_id, @book_habit, '2026-04-26 10:25:00'),
(@roses_id, @book_ml, '2026-04-27 09:50:00'),
(@roses_id, @book_sem, '2026-05-01 08:35:00'),
(@roses_id, @book_data, '2026-05-02 14:25:00'),
(@roses_id, @book_sem, '2026-05-02 20:00:00');

INSERT INTO favorite_categories (user_id, category_id, score) VALUES
(@roses_id, @cat_data, 0.95),
(@roses_id, @cat_lit, 0.82),
(@roses_id, @cat_psych, 0.68)
ON DUPLICATE KEY UPDATE score = VALUES(score);

-- ---------------------------------------------------------
-- Lịch sử mượn cho roses19
-- ---------------------------------------------------------
INSERT INTO borrow_requests (user_id, request_date, status, note, approved_by, approved_at, created_at) VALUES
(@roses_id, '2026-04-26 11:00:00', 'approved', 'Test recommendation: mượn sách văn học hiện đại', @admin_id, '2026-04-26 11:20:00', '2026-04-26 11:00:00'),
(@roses_id, '2026-04-27 15:15:00', 'approved', 'Test recommendation: mượn sách tìm kiếm ngữ nghĩa', @admin_id, '2026-04-27 15:40:00', '2026-04-27 15:15:00'),
(@roses_id, '2026-05-01 09:00:00', 'approved', 'Test prediction: mượn học máy', @admin_id, '2026-05-01 09:25:00', '2026-05-01 09:00:00'),
(@roses_id, '2026-05-02 16:30:00', 'pending', 'Test pending: phân tích dữ liệu mượn sách', NULL, NULL, '2026-05-02 16:30:00');

SET @req_lit := (
    SELECT id FROM borrow_requests
    WHERE user_id = @roses_id
      AND request_date = '2026-04-26 11:00:00'
      AND note = 'Test recommendation: mượn sách văn học hiện đại'
    ORDER BY id DESC
    LIMIT 1
);

SET @req_sem := (
    SELECT id FROM borrow_requests
    WHERE user_id = @roses_id
      AND request_date = '2026-04-27 15:15:00'
      AND note = 'Test recommendation: mượn sách tìm kiếm ngữ nghĩa'
    ORDER BY id DESC
    LIMIT 1
);

SET @req_ml := (
    SELECT id FROM borrow_requests
    WHERE user_id = @roses_id
      AND request_date = '2026-05-01 09:00:00'
      AND note = 'Test prediction: mượn học máy'
    ORDER BY id DESC
    LIMIT 1
);

SET @req_data := (
    SELECT id FROM borrow_requests
    WHERE user_id = @roses_id
      AND request_date = '2026-05-02 16:30:00'
      AND note = 'Test pending: phân tích dữ liệu mượn sách'
    ORDER BY id DESC
    LIMIT 1
);

INSERT INTO borrow_request_items (borrow_request_id, book_id, book_copy_id, quantity) VALUES
(@req_lit, @book_lit, @copy_lit_hp, 1),
(@req_sem, @book_sem, @copy_sem_vvt, 1),
(@req_ml, @book_ml, @copy_ml_vvt, 1),
(@req_data, @book_data, @copy_data_qt, 1);

INSERT INTO borrow_records (borrow_request_id, user_id, borrow_date, due_date, status, created_by, created_at) VALUES
(@req_lit, @roses_id, '2026-04-26 11:25:00', '2026-05-10 23:59:00', 'returned', @admin_id, '2026-04-26 11:25:00'),
(@req_sem, @roses_id, '2026-04-27 15:45:00', '2026-05-11 23:59:00', 'returned', @admin_id, '2026-04-27 15:45:00'),
(@req_ml, @roses_id, '2026-05-01 09:30:00', '2026-05-15 23:59:00', 'borrowing', @admin_id, '2026-05-01 09:30:00');

SET @record_lit := (
    SELECT id FROM borrow_records
    WHERE borrow_request_id = @req_lit
      AND user_id = @roses_id
    ORDER BY id DESC
    LIMIT 1
);

SET @record_sem := (
    SELECT id FROM borrow_records
    WHERE borrow_request_id = @req_sem
      AND user_id = @roses_id
    ORDER BY id DESC
    LIMIT 1
);

SET @record_ml := (
    SELECT id FROM borrow_records
    WHERE borrow_request_id = @req_ml
      AND user_id = @roses_id
    ORDER BY id DESC
    LIMIT 1
);

INSERT INTO borrow_record_items (borrow_record_id, book_id, book_copy_id, quantity, returned_quantity, item_status) VALUES
(@record_lit, @book_lit, @copy_lit_hp, 1, 1, 'returned'),
(@record_sem, @book_sem, @copy_sem_vvt, 1, 1, 'returned'),
(@record_ml, @book_ml, @copy_ml_vvt, 1, 0, 'borrowing');

INSERT INTO return_records (borrow_record_id, processed_by, return_date, note, created_at) VALUES
(@record_lit, @admin_id, '2026-05-01 17:10:00', 'Trả đúng hạn, dữ liệu test RCM', '2026-05-01 17:10:00'),
(@record_sem, @admin_id, '2026-05-02 11:30:00', 'Trả đúng hạn, dữ liệu semantic search', '2026-05-02 11:30:00');

-- ---------------------------------------------------------
-- Gợi ý sách đã sinh cho roses19
-- ---------------------------------------------------------
INSERT INTO recommendations (user_id, book_id, score, reason, generated_at) VALUES
(@roses_id, @book_data, 0.96, 'Bạn thường xem và mượn sách về machine learning, semantic search và phân tích dữ liệu.', '2026-05-02 18:00:00'),
(@roses_id, @book_sem, 0.91, 'Phù hợp với các truy vấn ngữ nghĩa về Python, embedding và tìm kiếm gần nghĩa.', '2026-05-02 18:05:00'),
(@roses_id, @book_habit, 0.73, 'Bạn có quan tâm đến thói quen đọc sách và phát triển bản thân.', '2026-05-02 18:10:00'),
(@roses_id, @book_lit, 0.70, 'Bạn từng tìm sách gần nghĩa với Mắt Biếc và truyện tuổi trẻ.', '2026-05-02 18:15:00');

-- ---------------------------------------------------------
-- Dự đoán nhu cầu mượn sách
-- ---------------------------------------------------------
INSERT INTO borrow_predictions (book_id, prediction_period, predicted_borrow_count, confidence_score, generated_at) VALUES
(@book_ml, '2026-05-01_to_2026-05-07', 8, 0.88, '2026-05-01 07:00:00'),
(@book_sem, '2026-05-01_to_2026-05-07', 7, 0.86, '2026-05-01 07:00:00'),
(@book_data, '2026-05-01_to_2026-05-07', 9, 0.91, '2026-05-02 07:00:00'),
(@book_lit, '2026-05-01_to_2026-05-07', 5, 0.76, '2026-05-02 07:00:00'),
(@book_habit, '2026-05-01_to_2026-05-07', 4, 0.72, '2026-05-02 07:00:00');

INSERT INTO notifications (user_id, title, content, type, is_read, created_at) VALUES
(@roses_id, 'Gợi ý sách mới cho bạn', 'Hệ thống đã gợi ý các sách về semantic search và học máy dựa trên lịch sử của bạn.', 'recommendation', FALSE, '2026-05-02 18:20:00');
