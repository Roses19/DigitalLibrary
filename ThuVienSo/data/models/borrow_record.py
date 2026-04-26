from datetime import datetime
from ThuVienSo import db


class BorrowRecord(db.Model):
    __tablename__ = "borrow_records"

    id = db.Column(db.Integer, primary_key=True)

    borrow_request_id = db.Column(
        db.Integer,
        db.ForeignKey("borrow_requests.id"),
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    borrow_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)

    status = db.Column(db.String(20), default="borrowing")

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    borrow_request = db.relationship(
        "BorrowRequest",
        backref="borrow_record"
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="borrow_records"
    )

    creator = db.relationship(
        "User",
        foreign_keys=[created_by],
        backref="created_borrow_records"
    )

    items = db.relationship(
        "BorrowRecordItem",
        back_populates="borrow_record",
        cascade="all, delete-orphan"
    )