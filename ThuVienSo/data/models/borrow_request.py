from datetime import datetime
from ThuVienSo import db


class BorrowRequest(db.Model):
    __tablename__ = "borrow_requests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="pending")

    note = db.Column(db.Text, nullable=True)

    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    reject_reason = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="borrow_requests"
    )

    approver = db.relationship(
        "User",
        foreign_keys=[approved_by],
        backref="approved_borrow_requests"
    )

    items = db.relationship(
        "BorrowRequestItem",
        back_populates="borrow_request",
        cascade="all, delete-orphan"
    )