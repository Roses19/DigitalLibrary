from ThuVienSo import db


class BorrowRequestItem(db.Model):
    __tablename__ = "borrow_request_items"

    id = db.Column(db.Integer, primary_key=True)
    borrow_request_id = db.Column(db.Integer, db.ForeignKey("borrow_requests.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    book = db.relationship("Book", backref="borrow_request_items")

    def __repr__(self):
        return f"<BorrowRequestItem req={self.borrow_request_id} book={self.book_id}>"
