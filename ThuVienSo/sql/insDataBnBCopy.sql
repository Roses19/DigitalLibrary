USE digital_library;

INSERT INTO roles (id, name, description) VALUES
(1, 'Độc giả', 'Người dùng mượn, trả và tìm kiếm sách'),
(2, 'Thủ thư', 'Nhân viên thư viện xử lý nghiệp vụ'),
(3, 'Quản trị', 'Quản lý toàn bộ hệ thống');

INSERT INTO users (id, role_id, full_name, email, username, password_hash, phone, status, created_at) VALUES
(1, 3, 'Nguyễn Đức Minh', 'admin@thuvien.vn', 'admin', 'hash_admin', '0901000001', 'active', '2026-01-02 08:00:00'),
(2, 2, 'Trần Thị Mai', 'maitt@thuvien.vn', 'maitt', 'hash_lib1', '0901000002', 'active', '2026-01-05 08:30:00'),
(3, 2, 'Lê Hoàng Phúc', 'phuclh@thuvien.vn', 'phuclh', 'hash_lib2', '0901000003', 'active', '2026-01-06 09:00:00'),
(4, 1, 'Phạm Ngọc Anh', 'ngocanh@gmail.com', 'ngocanh', 'hash1', '0912345601', 'active', '2026-02-01 10:12:00'),
(5, 1, 'Võ Minh Khoa', 'minhkhoa@gmail.com', 'minhkhoa', 'hash2', '0912345602', 'active', '2026-02-03 11:00:00'),
(6, 1, 'Nguyễn Bảo Châu', 'baochau@gmail.com', 'baochau', 'hash3', '0912345603', 'active', '2026-02-05 14:20:00'),
(7, 1, 'Trần Quốc Đạt', 'quocdat@gmail.com', 'quocdat', 'hash4', '0912345604', 'inactive', '2026-02-10 15:45:00'),
(8, 1, 'Lê Thu Hà', 'thuha@gmail.com', 'thuha', 'hash5', '0912345605', 'active', '2026-02-14 16:00:00'),
(9, 1, 'Đoàn Gia Huy', 'giahuy@gmail.com', 'giahuy', 'hash6', '0912345606', 'active', '2026-02-20 08:15:00'),
(10,1, 'Bùi Yến Nhi', 'yennhi@gmail.com', 'yennhi', 'hash7', '0912345607', 'active', '2026-03-01 09:10:00');

INSERT INTO categories (id, name, description) VALUES
(1, 'Văn học Việt Nam', 'Tác phẩm văn học trong nước'),
(2, 'Văn học nước ngoài', 'Tiểu thuyết và truyện dịch'),
(3, 'Công nghệ thông tin', 'Lập trình, AI, hệ thống'),
(4, 'Kỹ năng sống', 'Phát triển bản thân'),
(5, 'Thiếu nhi', 'Sách dành cho trẻ em');

INSERT INTO authors (id, name, biography) VALUES
(1, 'Nguyễn Nhật Ánh', 'Nhà văn nổi tiếng với nhiều tác phẩm tuổi thơ'),
(2, 'J.K. Rowling', 'Tác giả bộ Harry Potter'),
(3, 'Haruki Murakami', 'Nhà văn Nhật Bản hiện đại'),
(4, 'Dan Brown', 'Tác giả tiểu thuyết trinh thám'),
(5, 'Tô Hoài', 'Tác giả Dế Mèn Phiêu Lưu Ký');

INSERT INTO publishers (id, name, address, phone, email) VALUES
(1, 'NXB Trẻ', 'TP.HCM', '0281111111', 'contact@nxbtre.vn'),
(2, 'NXB Kim Đồng', 'Hà Nội', '0242222222', 'info@kimdong.vn'),
(3, 'Penguin Books', 'USA', '000111222', 'contact@penguin.com');

INSERT INTO books (id, category_id, publisher_id, title, isbn, description, publish_year, language, pages, created_by) VALUES
(1, 1, 1, 'Mắt Biếc', 'ISBN001', 'Câu chuyện tình buồn thời học sinh', 1990, 'vi', 250, 2),
(2, 2, 3, 'Harry Potter và Hòn đá Phù thủy', 'ISBN002', 'Cậu bé phù thủy nổi tiếng', 1997, 'en', 320, 2),
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