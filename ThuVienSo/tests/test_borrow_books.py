import os
import sys
import unittest

from sqlalchemy import text


# Đảm bảo Python tìm được index.py ở thư mục gốc project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class BorrowBooksFeatureTest(unittest.TestCase):
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

    def _login_as_roses19(self):
        from ThuVienSo.data.models.user import User

        with self.app.app_context():
            user = User.query.filter_by(username="roses19").first()

        if not user:
            self.skipTest("Test account roses19 is missing.")

        with self.client.session_transaction() as session:
            session["user_id"] = user.id
            session["username"] = user.username

        return user

    def test_borrow_history_page_loads_for_roses19(self):
        self._login_as_roses19()

        response = self.client.get("/borrow/history")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"borrow", response.data.lower())

    def test_branch_conflict_page_is_shown_for_other_branch_request(self):
        from ThuVienSo.data.models.book_copy import BookCopy
        from ThuVienSo.data.models.borrow_request import BorrowRequest
        from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem

        user = self._login_as_roses19()

        with self.app.app_context():
            pending_item = (
                BorrowRequestItem.query
                .join(BorrowRequest)
                .filter(
                    BorrowRequest.user_id == user.id,
                    BorrowRequest.status == "pending",
                    BorrowRequestItem.book_copy_id.isnot(None),
                )
                .first()
            )

            if not pending_item or not pending_item.book_copy:
                self.skipTest("No pending request with branch data is available.")

            other_copy = (
                BookCopy.query
                .filter(
                    BookCopy.book_id == pending_item.book_id,
                    BookCopy.branch_id != pending_item.book_copy.branch_id,
                    BookCopy.available_quantity > 0,
                )
                .first()
            )

            if not other_copy:
                self.skipTest("No other branch copy is available for conflict test.")

            book_id = pending_item.book_id
            other_branch_id = other_copy.branch_id

        response = self.client.get(
            f"/borrow/request/{book_id}?branch_id={other_branch_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"borrow-conflict-modal", response.data)
        self.assertIn(b"btn-change-branch", response.data)
        self.assertIn(b"btn-keep-branch", response.data)

    def test_borrow_form_loads_for_available_book_copy(self):
        from ThuVienSo.data.models.book_copy import BookCopy

        self._login_as_roses19()

        with self.app.app_context():
            copy = (
                BookCopy.query
                .filter(BookCopy.available_quantity > 0)
                .order_by(BookCopy.id.asc())
                .first()
            )

            if not copy:
                self.skipTest("No available book copy is available.")

            book_id = copy.book_id
            branch_id = copy.branch_id

        response = self.client.get(
            f"/borrow/request/{book_id}?branch_id={branch_id}"
        )

        self.assertIn(response.status_code, (200, 302))


if __name__ == "__main__":
    unittest.main()