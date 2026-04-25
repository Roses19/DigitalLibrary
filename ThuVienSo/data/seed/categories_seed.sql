USE digital_library;

INSERT INTO categories (id, name, description) VALUES
(1, 'Công nghệ', 'Sách về lập trình, CNTT, kỹ thuật phần mềm.'),
(2, 'Toán học', 'Giáo trình toán đại học và phổ thông.'),
(3, 'Khoa học', 'Vật lý, Hóa học, Sinh học đại cương.'),
(4, 'Văn học', 'Tác phẩm văn học trong và ngoài nước.'),
(5, 'Kinh tế', 'Kinh tế học, quản trị kinh doanh.')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description);

INSERT INTO authors (id, name, biography) VALUES
(1, 'Nguyễn Văn A', 'Tác giả sách lập trình và công nghệ.'),
(2, 'Trần Thị B', 'Tác giả giáo trình toán học.'),
(3, 'Lê Văn C', 'Tác giả sách cơ sở dữ liệu.'),
(4, 'Phạm Thị D', 'Tác giả sách khoa học đại cương.'),
(5, 'Hoàng Văn E', 'Tác giả sách kỹ thuật lập trình.')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    biography = VALUES(biography);

INSERT INTO publishers (id, name, address, phone, email) VALUES
(1, 'NXB Giáo dục Việt Nam', 'Hà Nội', '0240000000', 'contact@nxb-giaoduc.vn'),
(2, 'NXB Trẻ', 'TP. Hồ Chí Minh', '0280000000', 'contact@nxbtre.vn'),
(3, 'NXB Khoa học và Kỹ thuật', 'Hà Nội', '0241111111', 'contact@nxbkhkt.vn')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    address = VALUES(address),
    phone = VALUES(phone),
    email = VALUES(email);
