CREATE DATABASE digital_library
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE digital_library;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS borrow_predictions;
DROP TABLE IF EXISTS return_records;
DROP TABLE IF EXISTS borrow_record_items;
DROP TABLE IF EXISTS borrow_records;
DROP TABLE IF EXISTS borrow_request_items;
DROP TABLE IF EXISTS borrow_requests;
DROP TABLE IF EXISTS recommendations;
DROP TABLE IF EXISTS book_views;
DROP TABLE IF EXISTS favorite_categories;
DROP TABLE IF EXISTS search_histories;
DROP TABLE IF EXISTS book_authors;
DROP TABLE IF EXISTS book_copies;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS publishers;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. roles
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(255)
);

-- 2. users
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- 3. branches 🔥
CREATE TABLE branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. categories
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. authors
CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    biography TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. publishers
CREATE TABLE publishers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 7. books (KHÔNG có shelf + quantity)
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    publisher_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    description TEXT,
    cover_image VARCHAR(255),
    publish_year INT,
    language VARCHAR(50),
    pages INT,
    status VARCHAR(20) DEFAULT 'available',
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (publisher_id) REFERENCES publishers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 8. book_copies 🔥 (QUẢN LÝ KỆ + SỐ LƯỢNG)
CREATE TABLE book_copies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    branch_id INT NOT NULL,
    shelf_location VARCHAR(50),
    total_quantity INT DEFAULT 0,
    available_quantity INT DEFAULT 0,

    UNIQUE (book_id, branch_id),

    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- 9. book_authors
CREATE TABLE book_authors (
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- 10. search_histories
CREATE TABLE search_histories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    search_type VARCHAR(50) DEFAULT 'keyword',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 11. favorite_categories
CREATE TABLE favorite_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    score FLOAT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 12. book_views
CREATE TABLE book_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 13. recommendations
CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    score FLOAT DEFAULT 0,
    reason VARCHAR(255),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 14. borrow_requests
CREATE TABLE borrow_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    note TEXT,
    approved_by INT NULL,
    approved_at DATETIME NULL,
    reject_reason TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- 15. borrow_request_items
CREATE TABLE borrow_request_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_request_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT DEFAULT 1,
    FOREIGN KEY (borrow_request_id) REFERENCES borrow_requests(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 16. borrow_records
CREATE TABLE borrow_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_request_id INT NULL,
    user_id INT NOT NULL,
    borrow_date DATETIME NOT NULL,
    due_date DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'borrowing',
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrow_request_id) REFERENCES borrow_requests(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 17. borrow_record_items
CREATE TABLE borrow_record_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_record_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT DEFAULT 1,
    returned_quantity INT DEFAULT 0,
    item_status VARCHAR(20) DEFAULT 'borrowing',
    FOREIGN KEY (borrow_record_id) REFERENCES borrow_records(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 18. return_records
CREATE TABLE return_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_record_id INT NOT NULL,
    processed_by INT NULL,
    return_date DATETIME NOT NULL,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (borrow_record_id) REFERENCES borrow_records(id),
    FOREIGN KEY (processed_by) REFERENCES users(id)
);

-- 19. borrow_predictions
CREATE TABLE borrow_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    prediction_period VARCHAR(50),
    predicted_borrow_count INT DEFAULT 0,
    confidence_score FLOAT DEFAULT 0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 20. notifications
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255),
    content TEXT,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
-- =========================================
-- 21. library_rules (QUY ĐỊNH THƯ VIỆN)
-- =========================================
CREATE TABLE library_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,

    max_books_per_borrow INT DEFAULT 3,
    max_borrow_days INT DEFAULT 14,
    max_extend_times INT DEFAULT 1,

    fine_per_day DECIMAL(10,2) DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);