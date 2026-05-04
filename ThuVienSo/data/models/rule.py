from ThuVienSo import db
from datetime import datetime


class LibraryRule(db.Model):
    __tablename__ = "library_rules"

    id = db.Column(db.Integer, primary_key=True)

    max_books_per_borrow = db.Column(db.Integer, nullable=False, default=5)
    max_borrow_days = db.Column(db.Integer, nullable=False, default=15)

    # Số lần được gia hạn tối đa
    max_extend_times = db.Column(db.Integer, nullable=False, default=1)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )