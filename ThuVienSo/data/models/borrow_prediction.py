from datetime import datetime

from ThuVienSo import db


class BorrowPrediction(db.Model):
    __tablename__ = "borrow_predictions"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    prediction_period = db.Column(db.String(100))
    predicted_borrow_count = db.Column(db.Integer, default=0)
    confidence_score = db.Column(db.Float, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    book = db.relationship("Book", backref="borrow_predictions")
