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

    if category.books:
        flash(f'Không thể xóa "{category.name}" vì đang có sách.', "error")
        return redirect(url_for("book.categories"))

    db.session.delete(category)
    db.session.commit()

    flash(f'Đã xóa "{category.name}".', "success")
    return redirect(url_for("book.categories"))


# ================== SEARCH ==================
def build_book_query(keyword="", category_ids=None, publisher_ids=None, status=""):
    query = Book.query

    category_ids = category_ids or []
    publisher_ids = publisher_ids or []

    if keyword:
        query = query.outerjoin(Book.authors).filter(
            db.or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.isbn.ilike(f"%{keyword}%"),
                Author.name.ilike(f"%{keyword}%")
            )
        )

    if category_ids:
        query = query.filter(Book.category_id.in_(category_ids))

    if publisher_ids:
        query = query.filter(Book.publisher_id.in_(publisher_ids))

    if status == "available":
        query = query.filter(Book.available_quantity > 0)

    elif status == "unavailable":
        query = query.filter(Book.available_quantity <= 0)

    return query.distinct()


def search_books():
    keyword = request.args.get("q", "").strip()

    selected_categories = request.args.getlist("category")
    selected_publishers = request.args.getlist("publisher")
    selected_status = request.args.get("status", "").strip()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    searched = bool(
        keyword or selected_categories or selected_publishers or selected_status
    )

    if searched:
        books = build_book_query(
            keyword=keyword,
            category_ids=selected_categories,
            publisher_ids=selected_publishers,
            status=selected_status
        ).order_by(Book.created_at.desc()).all()
    else:
        books = []

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=searched,
        categories=categories,
        publishers=publishers,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_status=selected_status
    )


# ================== ADVANCED SEARCH ==================
def advanced_search_controller():
    keyword = request.args.get("q", "").strip()
    publisher_id = request.args.get("publisher_id", "").strip()
    category_id = request.args.get("category_id", "").strip()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

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

    books = query.distinct().order_by(Book.created_at.desc()).all()

    return render_template(
        "books/search.html",
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

# ================== BOOK LIST ==================
def get_book_list():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template("books/list.html", books=books)


# ================== ADMIN BOOK LIST ==================
def get_admin_book_list():
    books = Book.query.order_by(Book.created_at.desc()).all()
    categories = Category.query.all()
    publishers = Publisher.query.all()

    return render_template(
        "admin/books/index.html",
        books=books,
        categories=categories,
        publishers=publishers
    )


# ================== CREATE BOOK ==================
def create_book():
    title = request.form.get("title", "").strip()
    isbn = request.form.get("isbn", "").strip()
    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")
    quantity = request.form.get("quantity", 0)

    if not title:
        flash("Tên sách không được để trống", "error")
        return redirect(url_for("book.get_admin_book_list"))

    new_book = Book(
        title=title,
        isbn=isbn,
        category_id=int(category_id) if category_id else None,
        publisher_id=int(publisher_id) if publisher_id else None,
        quantity=int(quantity),
        available_quantity=int(quantity)
    )

    db.session.add(new_book)
    db.session.commit()

    flash("Thêm sách thành công", "success")
    return redirect(url_for("book.get_admin_book_list"))


# ================== UPDATE BOOK ==================
def update_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách", "error")
        return redirect(url_for("book.get_admin_book_list"))

    book.title = request.form.get("title", "").strip()
    book.isbn = request.form.get("isbn", "").strip()

    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")
    quantity = request.form.get("quantity", 0)

    book.category_id = int(category_id) if category_id else None
    book.publisher_id = int(publisher_id) if publisher_id else None

    # cập nhật số lượng
    book.quantity = int(quantity)

    # optional: sync available
    if book.available_quantity > book.quantity:
        book.available_quantity = book.quantity

    db.session.commit()

    flash("Cập nhật sách thành công", "success")
    return redirect(url_for("book.get_admin_book_list"))


# ================== DELETE BOOK ==================
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách", "error")
        return redirect(url_for("book.get_admin_book_list"))

    db.session.delete(book)
    db.session.commit()

    flash("Xóa sách thành công", "success")
    return redirect(url_for("book.get_admin_book_list"))