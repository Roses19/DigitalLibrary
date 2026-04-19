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
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS authors;
DROP TABLE IF EXISTS publishers;
DROP TABLE IF EXISTS categories;
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
    CONSTRAINT fk_users_role FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- 3. categories
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. authors
CREATE TABLE authors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    biography TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. publishers
CREATE TABLE publishers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. books
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
    shelf_location VARCHAR(50),
    total_quantity INT DEFAULT 0,
    available_quantity INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'available',
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_books_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_books_publisher FOREIGN KEY (publisher_id) REFERENCES publishers(id),
    CONSTRAINT fk_books_created_by FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 7. book_authors
CREATE TABLE book_authors (
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    CONSTRAINT fk_book_authors_book FOREIGN KEY (book_id) REFERENCES books(id),
    CONSTRAINT fk_book_authors_author FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- 8. search_histories
CREATE TABLE search_histories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    search_type VARCHAR(50) DEFAULT 'keyword',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_search_histories_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 9. favorite_categories
CREATE TABLE favorite_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    score FLOAT DEFAULT 0,
    CONSTRAINT fk_favorite_categories_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_favorite_categories_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- 10. book_views
CREATE TABLE book_views (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_book_views_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_book_views_book FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 11. recommendations
CREATE TABLE recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    book_id INT NOT NULL,
    score FLOAT DEFAULT 0,
    reason VARCHAR(255),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_recommendations_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_recommendations_book FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 12. borrow_requests
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
    CONSTRAINT fk_borrow_requests_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_borrow_requests_approved_by FOREIGN KEY (approved_by) REFERENCES users(id)
);

-- 13. borrow_request_items
CREATE TABLE borrow_request_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_request_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT DEFAULT 1,
    CONSTRAINT fk_borrow_request_items_request FOREIGN KEY (borrow_request_id) REFERENCES borrow_requests(id),
    CONSTRAINT fk_borrow_request_items_book FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 14. borrow_records
CREATE TABLE borrow_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_request_id INT NULL,
    user_id INT NOT NULL,
    borrow_date DATETIME NOT NULL,
    due_date DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'borrowing',
    created_by INT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_borrow_records_request FOREIGN KEY (borrow_request_id) REFERENCES borrow_requests(id),
    CONSTRAINT fk_borrow_records_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_borrow_records_created_by FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 15. borrow_record_items
CREATE TABLE borrow_record_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_record_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT DEFAULT 1,
    returned_quantity INT DEFAULT 0,
    item_status VARCHAR(20) DEFAULT 'borrowing',
    CONSTRAINT fk_borrow_record_items_record FOREIGN KEY (borrow_record_id) REFERENCES borrow_records(id),
    CONSTRAINT fk_borrow_record_items_book FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 16. return_records
CREATE TABLE return_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    borrow_record_id INT NOT NULL,
    processed_by INT NULL,
    return_date DATETIME NOT NULL,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_return_records_record FOREIGN KEY (borrow_record_id) REFERENCES borrow_records(id),
    CONSTRAINT fk_return_records_processed_by FOREIGN KEY (processed_by) REFERENCES users(id)
);

-- 17. borrow_predictions
CREATE TABLE borrow_predictions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    prediction_period VARCHAR(50) NOT NULL,
    predicted_borrow_count INT DEFAULT 0,
    confidence_score FLOAT DEFAULT 0,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_borrow_predictions_book FOREIGN KEY (book_id) REFERENCES books(id)
);

-- 18. notifications
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    type VARCHAR(50),
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id)
);