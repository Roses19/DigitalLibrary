-- DigitalLibrary full server setup SQL
-- Generated from ordered SQL fragments.
-- Run this file from the repository root with mysql client:
-- mysql -u <user> -p < ThuVienSo/sql/full_server_setup.sql

SOURCE ./ThuVienSo/sql/insBranchnBookCopy.sql;
SOURCE ./ThuVienSo/sql/insDataBnBCopy.sql;
SOURCE ./ThuVienSo/sql/insImgBook.sql;
SOURCE ./ThuVienSo/sql/fixBorrow.sql;
SOURCE ./ThuVienSo/sql/fixBranch.sql;
SOURCE ./ThuVienSo/sql/AddDataToRcm.sql;
SOURCE ./ThuVienSo/sql/AddBranchLibrarian.sql;
SOURCE ./ThuVienSo/sql/addDeleteBook.sql;
