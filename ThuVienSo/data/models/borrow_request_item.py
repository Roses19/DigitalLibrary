from ThuVienSo import db


class BorrowRequestItem(db.Model):
    __tablename__ = "borrow_request_items"

    id = db.Column(db.Integer, primary_key=True)

    borrow_request_id = db.Column(
        db.Integer,
        db.ForeignKey("borrow_requests.id"),
        nullable=False
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id"),
        nullable=False
    )

    book_copy_id = db.Column(
        db.Integer,
        db.ForeignKey("book_copies.id"),
        nullable=True
    )

    quantity = db.Column(db.Integer, nullable=False, default=1)

    borrow_request = db.relationship(
        "BorrowRequest",
        back_populates="items"
    )

    book = db.relationship("Book")

    book_copy = db.relationship("BookCopy")