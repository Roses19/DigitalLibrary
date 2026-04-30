import unittest
import dao
class TestLogin (unittest.TestCase):
    def test_login_success(self):
        self.assertTrue(dao.auth_user("admin", "123"))

    def test_login_fail(self):
        self.assertFalse(dao.auth_user("admin", "wrong"))

