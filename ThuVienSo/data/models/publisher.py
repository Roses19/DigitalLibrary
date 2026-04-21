from ThuVienSo import db


class Publisher(db.Model):
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Publisher {self.name}>"