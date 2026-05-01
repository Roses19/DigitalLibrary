import unittest


def lock_user(current_status):
    if current_status == "active":
        return "locked"

    return "active"


def create_user(username, users):
    for u in users:
        if u["username"] == username:
            return False

    users.append({
        "username": username
    })

    return True


class TestAdminManagement(unittest.TestCase):

    # Khóa user
    def test_lock_user(self):
        self.assertEqual(
            lock_user("active"),
            "locked"
        )

    # Mở khóa user
    def test_unlock_user(self):
        self.assertEqual(
            lock_user("locked"),
            "active"
        )

    # Tạo user thành công
    def test_create_user_success(self):
        users = []

        self.assertTrue(
            create_user("nhu", users)
        )

    # Username đã tồn tại
    def test_create_user_duplicate(self):
        users = [{
            "username": "admin"
        }]

        self.assertFalse(
            create_user("admin", users)
        )


if __name__ == "__main__":
    unittest.main()