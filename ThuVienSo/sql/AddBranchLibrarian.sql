USE digital_library;

ALTER TABLE users
ADD COLUMN branch_id INT NULL;

ALTER TABLE users
ADD CONSTRAINT fk_users_branch
FOREIGN KEY (branch_id) REFERENCES branches(id);
UPDATE users
SET branch_id = 1
WHERE username = 'maitt';

UPDATE users
SET branch_id = 2
WHERE username = 'phuclh';