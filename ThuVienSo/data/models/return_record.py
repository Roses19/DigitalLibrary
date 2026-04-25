from ThuVienSo import db


class ReturnRecord(db.Model):
    __tablename__ = "return_records"

    id = db.Column(db.Integer, primary_key=True)
    borrow_record_id = db.Column(db.Integer, db.ForeignKey("borrow_records.id"), nullable=False)
    processed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    return_date = db.Column(db.DateTime, nullable=False)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

    processor = db.relationship("User", foreign_keys=[processed_by])

    def __repr__(self):
        return f"<ReturnRecord {self.id} record={self.borrow_record_id}>"
