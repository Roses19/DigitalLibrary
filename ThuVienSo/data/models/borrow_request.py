from ThuVienSo import db


class BorrowRequest(db.Model):
    __tablename__ = "borrow_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    request_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default="pending")
    note = db.Column(db.Text)
    approved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    reject_reason = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime)

    user = db.relationship("User", foreign_keys=[user_id], backref="borrow_requests")
    approver = db.relationship("User", foreign_keys=[approved_by])
    items = db.relationship("BorrowRequestItem", backref="borrow_request", lazy="dynamic")

    def __repr__(self):
        return f"<BorrowRequest {self.id} - {self.status}>"
