(3, 2, 3, 'Kafka bên bờ biển', 'ISBN003', 'Tiểu thuyết siêu thực', 2002, 'jp', 400, 2),
(4, 3, 1, 'Học Python cơ bản', 'ISBN004', 'Sách lập trình Python', 2020, 'vi', 350, 2),
(5, 5, 2, 'Dế Mèn Phiêu Lưu Ký', 'ISBN005', 'Truyện thiếu nhi kinh điển', 1941, 'vi', 180, 2);


INSERT INTO book_authors (book_id, author_id) VALUES
(1,1),
(2,2),
(3,3),
(4,1),
(5,5);

INSERT INTO borrow_requests (id, user_id, status, note, approved_by, approved_at) VALUES
(1, 4, 'approved', 'Mượn đọc cuối tuần', 2, '2026-04-01 10:00:00'),
(2, 5, 'pending', 'Cần học lập trình', NULL, NULL),
(3, 6, 'rejected', 'Đã quá hạn trước đó', 2, '2026-04-02 09:00:00');

INSERT INTO borrow_records (id, borrow_request_id, user_id, borrow_date, due_date, status, created_by) VALUES
(1, 1, 4, '2026-04-01', '2026-04-10', 'borrowing', 2),
(2, NULL, 5, '2026-04-05', '2026-04-15', 'borrowing', 2);

INSERT INTO borrow_record_items (borrow_record_id, book_id, quantity, returned_quantity, item_status) VALUES
(1,1,1,1,'returned'),
(1,2,1,0,'borrowing'),
(2,4,1,0,'borrowing');

INSERT INTO return_records (borrow_record_id, processed_by, return_date, note) VALUES
(1, 2, '2026-04-09', 'Trả đúng hạn');

INSERT INTO notifications (user_id, title, content, type) VALUES
(4, 'Nhắc trả sách', 'Bạn sắp đến hạn trả sách "Mắt Biếc"', 'REMINDER'),
(5, 'Yêu cầu mượn sách', 'Yêu cầu của bạn đang chờ duyệt', 'INFO');

INSERT INTO branches (name, address) VALUES
('Chi nhánh Võ Văn Tần', 'Quận 3'),
('Chi nhánh Hiệp Phước', 'Nhà Bè');

INSERT INTO book_copies (book_id, branch_id, shelf_location, total_quantity, available_quantity) VALUES
(1, 1, 'A1-01', 5, 3),
(1, 2, 'A1-02', 2, 2),
(2, 1, 'B1-01', 10, 7),
(3, 2, 'C1-01', 4, 2);

INSERT INTO library_rules (max_books_per_borrow,max_borrow_days,max_extend_times,is_active) VALUES 
(5, 15, 2, 1);