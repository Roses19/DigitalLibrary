from ThuVienSo import db


class FavoriteCategory(db.Model):
    __tablename__ = "favorite_categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    score = db.Column(db.Float, default=0)

    user = db.relationship("User", backref="favorite_categories")
    category = db.relationship("Category", backref="favorite_users")
