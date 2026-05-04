import os
import sys
import unittest
from uuid import uuid4

from sqlalchemy import text
from werkzeug.routing import BuildError


# Đảm bảo Python tìm được index.py ở thư mục gốc project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class SecurityFeatureTest(unittest.TestCase):
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

    # ================== HELPERS ==================
    def _url_for_or_skip(self, endpoint, **kwargs):
        from flask import url_for

        try:
            with self.app.test_request_context():
                return url_for(endpoint, **kwargs)
        except BuildError:
            self.skipTest(f"Endpoint {endpoint} is missing.")

    def _find_user_by_roles(self, role_names):
        from ThuVienSo.data.models.user import User

        normalized_names = [name.lower() for name in role_names]

        user = (
            User.query
            .join(User.role)
            .filter(User.role.has())
            .filter(User.status == "active")
            .filter(User.role.has())
            .all()
        )

        for item in user:
            role_name = ""
            if item.role and item.role.name:
                role_name = item.role.name.strip().lower()

            if role_name in normalized_names:
                return item

        return None

    def _login_as_reader(self):
        role_names = [
            "độc giả",
            "doc gia",
            "reader",
            "user",
        ]

        with self.app.app_context():
            user = self._find_user_by_roles(role_names)

        if not user:
            self.skipTest("No active reader account is available.")

        with self.client.session_transaction() as session:
            session["user_id"] = user.id
            session["username"] = user.username

        return user

    def _delete_user_if_exists(self, username):
        from ThuVienSo.data.models.user import User

        user = User.query.filter_by(username=username).first()

        if user:
            self.db.session.delete(user)
            self.db.session.commit()

    def _delete_category_if_exists(self, name):
        from ThuVienSo.data.models.category import Category

        category = Category.query.filter_by(name=name).first()

        if category:
            self.db.session.delete(category)
            self.db.session.commit()

    def _reader_role_id_or_skip(self):
        from ThuVienSo.data.models.role import Role

        role = (
            Role.query
            .filter(Role.name.in_(["Độc giả", "doc gia", "reader", "user"]))
            .first()
        )

        if not role:
            role = Role.query.order_by(Role.id.asc()).first()

        if not role:
            self.skipTest("No role is available.")

        return role.id

    # ================== TEST 1: CHẶN TRUY CẬP ADMIN KHI CHƯA ĐĂNG NHẬP ==================
    def test_unauthenticated_user_cannot_create_user(self):
        """
        Người chưa đăng nhập không được phép tạo tài khoản qua endpoint admin.
        Nếu test này fail nghĩa là backend đang thiếu check quyền ở route /admin/users/create.
        """
        from ThuVienSo.data.models.user import User

        suffix = uuid4().hex[:8]
        username = f"security_guest_{suffix}"
        email = f"{username}@example.test"

        with self.app.app_context():
            role_id = self._reader_role_id_or_skip()
            self._delete_user_if_exists(username)

        response = self.client.post(
            "/admin/users/create",
            data={
                "full_name": "Security Guest",
                "username": username,
                "email": email,
                "phone": "0900000000",
                "password": "123456",
                "role_id": str(role_id),
                "status": "active",
                "next_url": "/admin?tab=users",
            },
            follow_redirects=False,
        )

        with self.app.app_context():
            created_user = User.query.filter_by(username=username).first()

            if created_user:
                self.db.session.delete(created_user)
                self.db.session.commit()

        self.assertIsNone(
            created_user,
            "Security issue: unauthenticated user was able to create an account."
        )

        self.assertIn(
            response.status_code,
            (302, 401, 403),
            "Unauthenticated admin action should redirect or be forbidden."
        )

    # ================== TEST 2: ĐỘC GIẢ KHÔNG ĐƯỢC THÊM DANH MỤC ==================
    def test_reader_cannot_create_category(self):
        """
        Độc giả chỉ được xem danh mục, không được thêm danh mục.
        """
        from ThuVienSo.data.models.category import Category

        self._login_as_reader()

        category_name = f"Security Category {uuid4().hex[:8]}"

        with self.app.app_context():
            self._delete_category_if_exists(category_name)

        create_url = self._url_for_or_skip("book.category_create")

        response = self.client.post(
            create_url,
            data={
                "name": category_name,
                "description": "This category should not be created by reader.",
            },
            follow_redirects=False,
        )

        with self.app.app_context():
            created_category = Category.query.filter_by(name=category_name).first()

            if created_category:
                self.db.session.delete(created_category)
                self.db.session.commit()

        self.assertIsNone(
            created_category,
            "Security issue: reader was able to create a category."
        )

        self.assertIn(
            response.status_code,
            (302, 401, 403),
            "Reader category creation should redirect or be forbidden."
        )

    # ================== TEST 3: SQL INJECTION SEARCH KHÔNG LÀM APP LỖI 500 ==================
    def test_search_sql_injection_payload_does_not_crash(self):
        """
        Search với payload giống SQL injection không được làm app crash.
        """
        payload = "' OR '1'='1"

        response = self.client.get(
            "/books/search",
            query_string={"q": payload},
        )

        self.assertLess(
            response.status_code,
            500,
            "Search endpoint crashed with SQL injection-like payload."
        )

        response_text = response.data.lower()

        dangerous_errors = [
            b"sqlalchemy.exc",
            b"pymysql.err",
            b"mysql syntax",
            b"traceback",
            b"operationalerror",
            b"programmingerror",
        ]

        for error_text in dangerous_errors:
            self.assertNotIn(
                error_text,
                response_text,
                f"Search response leaked database/internal error: {error_text}"
            )

    # ================== TEST 4: XSS PAYLOAD KHÔNG ĐƯỢC RENDER RAW ==================
    def test_search_xss_payload_is_escaped(self):
        """
        Từ khóa tìm kiếm dạng script không được render raw trong HTML.
        """
        payload = "<script>alert('xss')</script>"

        response = self.client.get(
            "/books/search",
            query_string={"q": payload},
        )

        self.assertLess(response.status_code, 500)

        self.assertNotIn(
            payload.encode("utf-8"),
            response.data,
            "Security issue: raw script tag was rendered in search result page."
        )

        self.assertNotIn(
            b"<script>alert",
            response.data.lower(),
            "Security issue: script tag appeared in rendered HTML."
        )

    # ================== TEST 5: CHƯA ĐĂNG NHẬP KHÔNG ĐƯỢC XEM LỊCH SỬ MƯỢN ==================
    def test_unauthenticated_user_cannot_view_borrow_history(self):
        """
        Người chưa đăng nhập không được xem lịch sử mượn sách cá nhân.
        """
        response = self.client.get(
            "/borrow/history",
            follow_redirects=False,
        )

        self.assertIn(
            response.status_code,
            (302, 401, 403),
            "Security issue: unauthenticated user can access borrow history."
        )

    # ================== TEST 6: ĐỘC GIẢ KHÔNG ĐƯỢC VÀO TRANG QUẢN TRỊ NGƯỜI DÙNG ==================
    def test_reader_cannot_access_admin_users_page(self):
        """
        Độc giả không được truy cập trang quản lý người dùng.
        """
        self._login_as_reader()

        response = self.client.get(
            "/admin?tab=users",
            follow_redirects=False,
        )

        if response.status_code == 200:
            page = response.data.lower()

            self.assertNotIn(
                b"/admin/users/create",
                page,
                "Security issue: reader can see user creation action."
            )

            self.assertNotIn(
                b"quan ly nguoi dung",
                page,
                "Security issue: reader can access admin user management page."
            )

            self.assertNotIn(
                "quản lý người dùng".encode("utf-8"),
                response.data,
                "Security issue: reader can access admin user management page."
            )
        else:
            self.assertIn(response.status_code, (302, 401, 403))


if __name__ == "__main__":
    unittest.main()