USE digital_library;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS branch_id INT NULL;

SET @fk_users_branch_exists := (
    SELECT COUNT(*)
    FROM information_schema.TABLE_CONSTRAINTS
    WHERE CONSTRAINT_SCHEMA = DATABASE()
      AND TABLE_NAME = 'users'
      AND CONSTRAINT_NAME = 'fk_users_branch'
);

SET @sql_users_branch_fk := IF(
    @fk_users_branch_exists = 0,
    'ALTER TABLE users ADD CONSTRAINT fk_users_branch FOREIGN KEY (branch_id) REFERENCES branches(id)',
    'SELECT 1'
);
PREPARE stmt_users_branch_fk FROM @sql_users_branch_fk;
EXECUTE stmt_users_branch_fk;
DEALLOCATE PREPARE stmt_users_branch_fk;

UPDATE users
SET branch_id = 1
WHERE username = 'maitt';

UPDATE users
SET branch_id = 2
WHERE username = 'phuclh';
