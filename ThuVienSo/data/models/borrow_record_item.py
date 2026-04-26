from ThuVienSo import db


class BorrowRecordItem(db.Model):
    __tablename__ = "borrow_record_items"

    id = db.Column(db.Integer, primary_key=True)

    borrow_record_id = db.Column(
        db.Integer,
        db.ForeignKey("borrow_records.id"),
        nullable=False
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id"),
        nullable=False
    )

    quantity = db.Column(db.Integer, default=1)
    returned_quantity = db.Column(db.Integer, default=0)

    item_status = db.Column(db.String(20), default="borrowing")

    borrow_record = db.relationship(
        "BorrowRecord",
        back_populates="items"
    )

    book = db.relationship(
        "Book",
        backref="borrow_record_items"
    )