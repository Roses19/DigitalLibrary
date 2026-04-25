from ThuVienSo import db
class BookCopy(db.Model):
    __tablename__ = "book_copies"

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"))
    branch_id = db.Column(db.Integer, db.ForeignKey("branches.id"))

    shelf_location = db.Column(db.String(50))
    total_quantity = db.Column(db.Integer)
    available_quantity = db.Column(db.Integer)

    book = db.relationship("Book", back_populates="copies")