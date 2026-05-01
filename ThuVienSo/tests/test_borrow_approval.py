import unittest


def approve_borrow_request(status, quantity, available_quantity):
    if status != "pending":
        return False

    if quantity > available_quantity:
        return False

    return True


class TestBorrowApproval(unittest.TestCase):

    # Duyệt thành công
    def test_approve_success(self):
        self.assertTrue(
            approve_borrow_request(
                "pending",
                1,
                5
            )
        )

    # Không đủ sách
    def test_approve_not_enough_books(self):
        self.assertFalse(
            approve_borrow_request(
                "pending",
                10,
                2
            )
        )

    # Request đã duyệt
    def test_approve_invalid_status(self):
        self.assertFalse(
            approve_borrow_request(
                "approved",
                1,
                5
            )
        )


if __name__ == "__main__":
    unittest.main()