from ThuVienSo import db
from ThuVienSo.data.models.book_author import book_authors


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id"), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    publish_year = db.Column(db.Integer)
    language = db.Column(db.String(50))
    pages = db.Column(db.Integer)
    shelf_location = db.Column(db.String(50))
    total_quantity = db.Column(db.Integer, default=0)
    available_quantity = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="available")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    category = db.relationship("Category", backref="books")
    publisher = db.relationship("Publisher", backref="books")
    authors = db.relationship(
        "Author",
        secondary=book_authors,
        backref=db.backref("books", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<Book {self.title}>"