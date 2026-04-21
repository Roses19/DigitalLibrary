from flask import request, render_template, redirect, url_for, flash
from ThuVienSo import db
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.author import Author


# ================== HOME ==================
def get_home_books():
    return Book.query.order_by(Book.created_at.desc()).limit(4).all()


# ================== CATEGORY ==================
def get_categories():
    categories = Category.query.all()
    return render_template("books/categories.html", categories=categories)


def create_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    exists = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
    if exists:
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    new_category = Category(name=name, description=description)
    db.session.add(new_category)
    db.session.commit()

    flash(f'Đã thêm danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def update_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    exists = Category.query.filter(
        db.func.lower(Category.name) == name.lower(),
        Category.id != category_id
    ).first()

    if exists:
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    category.name = name
    category.description = description
    db.session.commit()

    flash(f'Đã cập nhật danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def delete_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    if category.books:  # dùng relationship
        flash(f'Không thể xóa "{category.name}" vì đang có sách.', "error")
        return redirect(url_for("book.categories"))

    db.session.delete(category)
    db.session.commit()

    flash(f'Đã xóa "{category.name}".', "success")
    return redirect(url_for("book.categories"))


# ================== SEARCH ==================
def build_book_query(keyword="", publisher_id="", category_id=""):
    query = Book.query

    if keyword:
        query = query.outerjoin(Book.authors).filter(
            db.or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.isbn.ilike(f"%{keyword}%"),
                Author.name.ilike(f"%{keyword}%")
            )
        )

    if publisher_id:
        query = query.filter(Book.publisher_id == int(publisher_id))

    if category_id:
        query = query.filter(Book.category_id == int(category_id))

    return query


def search_books():
    keyword = request.args.get("q", "").strip()

    if not keyword:
        return render_template("books/search.html", books=[], keyword="", searched=False)

    books = build_book_query(keyword=keyword) \
        .order_by(Book.created_at.desc()) \
        .all()

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=True
    )


# ================== ADVANCED SEARCH ==================
def advanced_search_controller():
    keyword = request.args.get("q", "").strip()
    publisher_id = request.args.get("publisher_id", "").strip()
    category_id = request.args.get("category_id", "").strip()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    books = build_book_query(keyword, publisher_id, category_id) \
        .order_by(Book.created_at.desc()) \
        .all()

    return render_template(
        "books/advanced_search.html",
        books=books,
        categories=categories,
        publishers=publishers,
        keyword=keyword,
        publisher_id=publisher_id,
        category_id=category_id
    )


# ================== DETAIL ==================
def get_book_detail(book_id):
    book = Book.query.get(book_id)

    if not book:
        return render_template("books/detail.html", book=None)

    return render_template("books/detail.html", book=book)