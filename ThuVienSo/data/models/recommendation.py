from datetime import datetime

from ThuVienSo import db


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    score = db.Column(db.Float, default=0)
    reason = db.Column(db.Text)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="recommendations")
    book = db.relationship("Book", backref="recommendations")
