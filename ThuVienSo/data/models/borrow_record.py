from ThuVienSo import db


class BorrowRecord(db.Model):
    __tablename__ = "borrow_records"

    id = db.Column(db.Integer, primary_key=True)
    borrow_request_id = db.Column(db.Integer, db.ForeignKey("borrow_requests.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    borrow_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default="borrowing")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime)

    user = db.relationship("User", foreign_keys=[user_id], backref="borrow_records")
    creator = db.relationship("User", foreign_keys=[created_by])
    items = db.relationship("BorrowRecordItem", backref="borrow_record", lazy="dynamic")
    return_records = db.relationship("ReturnRecord", backref="borrow_record", lazy="dynamic")

    def __repr__(self):
        return f"<BorrowRecord {self.id} - {self.status}>"
