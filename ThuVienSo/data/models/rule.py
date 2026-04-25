from ThuVienSo import db
class LibraryRule(db.Model):
    __tablename__ = 'library_rules'

    id = db.Column(db.Integer, primary_key=True)

    max_books_per_borrow = db.Column(db.Integer, default=3)
    max_borrow_days = db.Column(db.Integer, default=14)
    max_extend_times = db.Column(db.Integer, default=1)

    is_active = db.Column(db.Boolean, default=True)