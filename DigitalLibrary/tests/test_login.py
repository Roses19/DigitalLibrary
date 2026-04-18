import unittest
from DigitalLibrary import dao
from DigitalLibrary.dao import auth_user


class TestLogin (unittest.TestCase):
    def test_case_1(self):
        self.assertTrue(dao.auth_user("user", 123))

    def test_case_2(self):
        self.assertFalse(auth_user("admin",123))


if __name__=="__main__":
    unittest.main()

