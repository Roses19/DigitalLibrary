import json
import unittest

def auth_user(username, password):
    users = [
        {
            "username": "admin",
            "password": "123"
        },
        {
            "username": "nhu",
            "password": "456"
        }
    ]

    for u in users:
        if u["username"] == username and u["password"] == password:
            return True

    return False


if __name__=="__main__":
    unittest.main()