import unittest


def register(users, username, email):

    for u in users:
        if u["username"] == username:
            return False

    users.append({
        "username": username,
        "email": email
    })

    return True


class TestRegister(unittest.TestCase):

    def test_register_success(self):
        users = []

        self.assertTrue(
            register(users, "nhu", "nhu@gmail.com")
        )

    def test_register_duplicate(self):
        users = [{
            "username": "admin",
            "email": "admin@gmail.com"
        }]

        self.assertFalse(
            register(users, "admin", "new@gmail.com")
        )


if __name__ == "__main__":
    unittest.main()