import os
import sys
import unittest
from uuid import uuid4

from sqlalchemy import text


# Đảm bảo Python tìm được index.py ở thư mục gốc project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class UserManagementFeatureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from index import app
        from ThuVienSo import db

        cls.app = app
        cls.db = db
        cls.client = app.test_client()
        cls.app.config["TESTING"] = True

        with cls.app.app_context():
            try:
                cls.db.session.execute(text("SELECT 1"))
            except Exception as exc:
                raise unittest.SkipTest(f"Database is not ready: {exc}") from exc

    def _reader_role(self):
        from ThuVienSo.data.models.role import Role

        role = (
            Role.query
            .filter(Role.name.in_(["Độc giả", "doc gia", "reader"]))
            .first()
        )

        if not role:
            role = Role.query.order_by(Role.id.asc()).first()

        if not role:
            self.skipTest("No role is available for creating a user.")

        return role

    def _delete_user_if_exists(self, username):
        from ThuVienSo.data.models.user import User

        user = User.query.filter_by(username=username).first()

        if user:
            self.db.session.delete(user)
            self.db.session.commit()

    def test_admin_users_tab_loads(self):
        response = self.client.get("/admin?tab=users")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"users", response.data.lower())

    def test_create_update_lock_unlock_delete_user_flow(self):
        from ThuVienSo.data.models.user import User

        suffix = uuid4().hex[:8]
        username = f"test_reader_{suffix}"
        edited_username = f"{username}_edit"
        email = f"{username}@example.test"
        edited_email = f"{edited_username}@example.test"

        with self.app.app_context():
            role = self._reader_role()
            self._delete_user_if_exists(username)
            self._delete_user_if_exists(edited_username)
            role_id = role.id

        try:
            response = self.client.post(
                "/admin/users/create",
                data={
                    "full_name": "Temporary Reader",
                    "username": username,
                    "email": email,
                    "phone": "0900000000",
                    "password": "123456",
                    "role_id": str(role_id),
                    "status": "active",
                    "next_url": "/admin?tab=users",
                },
            )

            self.assertEqual(response.status_code, 302)

            with self.app.app_context():
                user = User.query.filter_by(username=username).first()
                self.assertIsNotNone(user)
                user_id = user.id

            response = self.client.post(
                f"/admin/users/{user_id}/edit",
                data={
                    "full_name": "Temporary Reader Edited",
                    "username": edited_username,
                    "email": edited_email,
                    "phone": "0911111111",
                    "password": "",
                    "role_id": str(role_id),
                    "status": "active",
                    "next_url": "/admin?tab=users",
                },
            )

            self.assertEqual(response.status_code, 302)

            with self.app.app_context():
                user = self.db.session.get(User, user_id)
                self.assertIsNotNone(user)
                self.assertEqual(user.username, edited_username)
                self.assertEqual(user.email, edited_email)

            lock_response = self.client.post(
                f"/admin/users/{user_id}/status",
                data={"next_url": "/admin?tab=users"},
            )

            self.assertEqual(lock_response.status_code, 302)

            with self.app.app_context():
                user = self.db.session.get(User, user_id)
                self.assertIsNotNone(user)
                self.assertEqual(user.status, "locked")

            unlock_response = self.client.post(
                f"/admin/users/{user_id}/status",
                data={"next_url": "/admin?tab=users"},
            )

            self.assertEqual(unlock_response.status_code, 302)

            with self.app.app_context():
                user = self.db.session.get(User, user_id)
                self.assertIsNotNone(user)
                self.assertEqual(user.status, "active")

            delete_response = self.client.post(
                f"/admin/users/{user_id}/delete",
                data={"next_url": "/admin?tab=users"},
            )

            self.assertEqual(delete_response.status_code, 302)

            with self.app.app_context():
                self.assertIsNone(self.db.session.get(User, user_id))

        finally:
            with self.app.app_context():
                self._delete_user_if_exists(username)
                self._delete_user_if_exists(edited_username)


if __name__ == "__main__":
    unittest.main()