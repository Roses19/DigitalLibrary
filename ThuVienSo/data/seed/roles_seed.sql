USE digital_library;

INSERT INTO roles (id, name, description) VALUES
(1, 'admin', 'Quản trị viên hệ thống'),
(2, 'reader', 'Bạn đọc thư viện')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description);

INSERT INTO users (id, role_id, full_name, email, username, password_hash, phone, status) VALUES
(1, 1, 'Quản trị viên', 'admin@library.local', 'admin', 'admin123', '0900000000', 'active'),
(2, 2, 'Nguyễn Phương Anh', 'phuonganh@library.local', 'phuonganh', '123456', '0912345678', 'active')
ON DUPLICATE KEY UPDATE
    role_id = VALUES(role_id),
    full_name = VALUES(full_name),
    email = VALUES(email),
    username = VALUES(username),
    password_hash = VALUES(password_hash),
    phone = VALUES(phone),
    status = VALUES(status);
