from datetime import datetime

from ThuVienSo import db


class BookView(db.Model):
    __tablename__ = "book_views"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="book_views")
    book = db.relationship("Book", backref="views")
