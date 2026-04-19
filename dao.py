import json
import unittest

def auth_user(username, password):
    with open("../data/users.json", encoding="uft-8") as f:
        users = json.load(f)
        for u in users:
            if u["username"] == username and u["password"] == password:
                return True

    return False


if __name__=="__main__":
    unittest.main()