import unittest
from DigitalLibrary import dao
class TestLogin (unittest.TestCase):
    def test_case_1(self):
        self.assertTrue(dao.auth_user("user", 123))

