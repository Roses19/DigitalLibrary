from ThuVienSo import db


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    biography = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"<Author {self.name}>"