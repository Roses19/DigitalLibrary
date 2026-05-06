USE digital_library;

ALTER TABLE borrow_request_items
ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;

ALTER TABLE borrow_record_items
ADD COLUMN IF NOT EXISTS book_copy_id INT NULL AFTER book_id;

SET @fk_bri_exists := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'borrow_request_items'
      AND CONSTRAINT_NAME = 'fk_borrow_request_items_book_copy'
);

SET @sql_bri_fk := IF(
    @fk_bri_exists = 0,
    'ALTER TABLE borrow_request_items ADD CONSTRAINT fk_borrow_request_items_book_copy FOREIGN KEY (book_copy_id) REFERENCES book_copies(id) ON DELETE SET NULL',
    'SELECT 1'
);
PREPARE stmt_bri_fk FROM @sql_bri_fk;
EXECUTE stmt_bri_fk;
DEALLOCATE PREPARE stmt_bri_fk;

SET @fk_brr_exists := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'borrow_record_items'
      AND CONSTRAINT_NAME = 'fk_borrow_record_items_book_copy'
);

SET @sql_brr_fk := IF(
    @fk_brr_exists = 0,
    'ALTER TABLE borrow_record_items ADD CONSTRAINT fk_borrow_record_items_book_copy FOREIGN KEY (book_copy_id) REFERENCES book_copies(id) ON DELETE SET NULL',
    'SELECT 1'
);
PREPARE stmt_brr_fk FROM @sql_brr_fk;
EXECUTE stmt_brr_fk;
DEALLOCATE PREPARE stmt_brr_fk;
