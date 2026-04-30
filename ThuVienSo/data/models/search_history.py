from datetime import datetime

from ThuVienSo import db


class SearchHistory(db.Model):
    __tablename__ = "search_histories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    search_type = db.Column(db.String(50), default="keyword")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="search_histories")
