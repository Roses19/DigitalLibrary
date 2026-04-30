ALTER TABLE borrow_request_items
ADD COLUMN book_copy_id INT NULL AFTER book_id;

ALTER TABLE borrow_record_items
ADD COLUMN book_copy_id INT NULL AFTER book_id;

ALTER TABLE borrow_request_items
ADD CONSTRAINT fk_borrow_request_items_book_copy
FOREIGN KEY (book_copy_id) REFERENCES book_copies(id)
ON DELETE SET NULL;

ALTER TABLE borrow_record_items
ADD CONSTRAINT fk_borrow_record_items_book_copy
FOREIGN KEY (book_copy_id) REFERENCES book_copies(id)
ON DELETE SET NULL;