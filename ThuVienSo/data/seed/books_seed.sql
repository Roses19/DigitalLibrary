USE digital_library;

INSERT INTO books
(id, category_id, publisher_id, title, isbn, description, cover_image, publish_year, language, pages, shelf_location, total_quantity, available_quantity, status, created_by)
VALUES
(1, 1, 3, 'Lập trình Python cơ bản', '9780000000011', 'Sách hướng dẫn lập trình Python từ cơ bản đến nâng cao.', 'https://placehold.co/200x280?text=Python', 2024, 'Tiếng Việt', 250, 'A1-01', 5, 5, 'available', 1),
(2, 2, 1, 'Giải tích 1', '9780000000028', 'Giáo trình giải tích dành cho sinh viên đại học.', 'https://placehold.co/200x280?text=Giai+Tich', 2023, 'Tiếng Việt', 320, 'B1-02', 3, 3, 'available', 1),
(3, 1, 3, 'Nhập môn Cơ sở dữ liệu', '9780000000035', 'Tổng quan về hệ quản trị cơ sở dữ liệu quan hệ.', 'https://placehold.co/200x280?text=CSDL', 2024, 'Tiếng Việt', 280, 'A1-03', 4, 0, 'available', 1),
(4, 3, 1, 'Vật lý đại cương', '9780000000042', 'Giáo trình vật lý đại cương cho sinh viên năm nhất.', 'https://placehold.co/200x280?text=Vat+Ly', 2022, 'Tiếng Việt', 300, 'C2-01', 2, 2, 'available', 1),
(5, 1, 2, 'Kỹ thuật lập trình', '9780000000059', 'Các kỹ thuật lập trình hiệu quả và tối ưu.', 'https://placehold.co/200x280?text=KTLT', 2024, 'Tiếng Việt', 260, 'A2-04', 1, 1, 'available', 1),
(6, 4, 2, 'Dế Mèn Phiêu Lưu Ký', '9780000000066', 'Tác phẩm văn học thiếu nhi kinh điển của Việt Nam.', 'https://placehold.co/200x280?text=De+Men', 2021, 'Tiếng Việt', 180, 'D1-01', 6, 4, 'available', 1),
(7, 5, 2, 'Kinh tế học nhập môn', '9780000000073', 'Các khái niệm cơ bản về kinh tế học và thị trường.', 'https://placehold.co/200x280?text=Kinh+Te', 2023, 'Tiếng Việt', 240, 'E1-01', 3, 3, 'available', 1)
ON DUPLICATE KEY UPDATE
    category_id = VALUES(category_id),
    publisher_id = VALUES(publisher_id),
    title = VALUES(title),
    isbn = VALUES(isbn),
    description = VALUES(description),
    cover_image = VALUES(cover_image),
    publish_year = VALUES(publish_year),
    language = VALUES(language),
    pages = VALUES(pages),
    shelf_location = VALUES(shelf_location),
    total_quantity = VALUES(total_quantity),
    available_quantity = VALUES(available_quantity),
    status = VALUES(status),
    created_by = VALUES(created_by);

INSERT INTO book_authors (book_id, author_id) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4),
(5, 5),
(6, 5),
(7, 2)
ON DUPLICATE KEY UPDATE
    book_id = VALUES(book_id),
    author_id = VALUES(author_id);
