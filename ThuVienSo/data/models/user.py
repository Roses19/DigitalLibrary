from ThuVienSo import db
from werkzeug.security import check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20))

    role = db.relationship("Role")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)