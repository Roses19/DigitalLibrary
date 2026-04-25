from ThuVienSo import db

class Branch(db.Model):
    __tablename__ = "branches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))

    copies = db.relationship("BookCopy", backref="branch", lazy=True)