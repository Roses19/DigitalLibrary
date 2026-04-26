from flask import request, render_template, redirect, url_for, flash
from ThuVienSo import db

from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.author import Author

from ThuVienSo.controller.borrow_controller import get_user_borrow_states


# ================== HELPER ==================
def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def admin_books_redirect():
    next_url = request.form.get("next_url")

    if next_url:
        return redirect(next_url)

    return redirect("/admin?tab=books")


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

    new_category = Category(
        name=name,
        description=description
    )

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


# ================== SEARCH HELPER ==================
def to_int_list(values):
    result = []

    for value in values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            pass

    return result


def get_book_status_value(book):
    available_quantity = getattr(book, "available_quantity", 0) or 0

    if available_quantity > 0:
        return "available"

    return "unavailable"


def get_status_label(status_value):
    if status_value == "available":
        return "Còn sách"

    if status_value == "unavailable":
        return "Đã hết"

    return status_value


def get_status_options_from_books(books):
    seen = set()
    status_options = []

    for book in books:
        status_value = get_book_status_value(book)

        if status_value not in seen:
            seen.add(status_value)
            status_options.append({
                "value": status_value,
                "label": get_status_label(status_value)
            })

    status_options.sort(
        key=lambda item: 0 if item["value"] == "available" else 1
    )

    return status_options


def get_filter_options_from_books(books):
    category_ids = []
    publisher_ids = []

    for book in books:
        if book.category_id and book.category_id not in category_ids:
            category_ids.append(book.category_id)

        if book.publisher_id and book.publisher_id not in publisher_ids:
            publisher_ids.append(book.publisher_id)

    categories = []
    publishers = []

    if category_ids:
        categories = (
            Category.query
            .filter(Category.id.in_(category_ids))
            .order_by(Category.name.asc())
            .all()
        )

    if publisher_ids:
        publishers = (
            Publisher.query
            .filter(Publisher.id.in_(publisher_ids))
            .order_by(Publisher.name.asc())
            .all()
        )

    status_options = get_status_options_from_books(books)

    return categories, publishers, status_options


def build_book_query(keyword="", category_ids=None, publisher_ids=None, statuses=None):
    query = Book.query

    category_ids = to_int_list(category_ids or [])
    publisher_ids = to_int_list(publisher_ids or [])
    statuses = statuses or []

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

    if statuses:
        if "available" in statuses and "unavailable" not in statuses:
            query = query.filter(Book.available_quantity > 0)

        elif "unavailable" in statuses and "available" not in statuses:
            query = query.filter(Book.available_quantity <= 0)

    return query.distinct()


# ================== SEARCH ==================
def search_books():
    keyword = request.args.get("q", "").strip()

    selected_categories = request.args.getlist("category")
    selected_publishers = request.args.getlist("publisher")
    selected_statuses = request.args.getlist("status")

    filter_applied = request.args.get("filter") == "1"

    searched = bool(
        keyword or selected_categories or selected_publishers or selected_statuses
    )

    if keyword:
        matched_books = (
            build_book_query(keyword=keyword)
            .order_by(Book.created_at.desc())
            .all()
        )
    else:
        matched_books = []

    if keyword:
        categories, publishers, status_options = get_filter_options_from_books(matched_books)

        if not filter_applied:
            selected_categories = [str(category.id) for category in categories]
            selected_publishers = [str(publisher.id) for publisher in publishers]
            selected_statuses = [status["value"] for status in status_options]

    else:
        categories = Category.query.order_by(Category.name.asc()).all()
        publishers = Publisher.query.order_by(Publisher.name.asc()).all()

        all_books = Book.query.all()
        status_options = get_status_options_from_books(all_books)

    if searched:
        if keyword and not filter_applied:
            books = matched_books
        else:
            books = (
                build_book_query(
                    keyword=keyword,
                    category_ids=selected_categories,
                    publisher_ids=selected_publishers,
                    statuses=selected_statuses
                )
                .order_by(Book.created_at.desc())
                .all()
            )
    else:
        books = []

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=searched,
        categories=categories,
        publishers=publishers,
        status_options=status_options,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_statuses=selected_statuses,
        user_borrow_states=get_user_borrow_states()
    )


# ================== ADVANCED SEARCH ==================
def advanced_search_controller():
    keyword = request.args.get("q", "").strip()
    publisher_id = request.args.get("publisher_id", "").strip()
    category_id = request.args.get("category_id", "").strip()

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

    if keyword:
        categories, publishers, status_options = get_filter_options_from_books(books)
    else:
        categories = Category.query.order_by(Category.name.asc()).all()
        publishers = Publisher.query.order_by(Publisher.name.asc()).all()
        status_options = get_status_options_from_books(Book.query.all())

    selected_categories = [category_id] if category_id else []
    selected_publishers = [publisher_id] if publisher_id else []
    selected_statuses = [status["value"] for status in status_options] if keyword else []

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=True,
        categories=categories,
        publishers=publishers,
        status_options=status_options,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_statuses=selected_statuses,
        user_borrow_states=get_user_borrow_states()
    )


# ================== DETAIL ==================
def get_book_detail(book_id):
    book = Book.query.get(book_id)

    if not book:
        return render_template("books/detail.html", book=None)

    return render_template(
        "books/detail.html",
        book=book,
        user_borrow_states=get_user_borrow_states()
    )


# ================== BOOK LIST ==================
def get_book_list():
    books = Book.query.order_by(Book.created_at.desc()).all()

    return render_template(
        "books/list.html",
        books=books,
        user_borrow_states=get_user_borrow_states()
    )


# ================== ADMIN BOOK LIST ==================
def get_admin_book_list():
    books = Book.query.order_by(Book.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    return redirect("/admin?tab=books"
)


# ================== CREATE BOOK ==================
def create_book():
    title = request.form.get("title", "").strip()
    isbn = request.form.get("isbn", "").strip()

    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")

    available_quantity = safe_int(
        request.form.get("available_quantity") or request.form.get("quantity"),
        0
    )

    if not title:
        flash("Tên sách không được để trống.", "error")
        return admin_books_redirect()

    if available_quantity < 0:
        available_quantity = 0

    new_book = Book(
        title=title,
        isbn=isbn,
        category_id=int(category_id) if category_id else None,
        publisher_id=int(publisher_id) if publisher_id else None,
        available_quantity=available_quantity
    )

    # Nếu model có total_quantity thì set luôn cho đồng bộ.
    if hasattr(new_book, "total_quantity"):
        new_book.total_quantity = available_quantity

    db.session.add(new_book)
    db.session.commit()

    flash("Thêm sách thành công.", "success")
    return admin_books_redirect()


# ================== UPDATE BOOK ==================
def update_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return admin_books_redirect()

    title = request.form.get("title", "").strip()
    isbn = request.form.get("isbn", "").strip()

    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")

    available_quantity = safe_int(
        request.form.get("available_quantity") or request.form.get("quantity"),
        0
    )

    if not title:
        flash("Tên sách không được để trống.", "error")
        return admin_books_redirect()

    if available_quantity < 0:
        available_quantity = 0

    book.title = title
    book.isbn = isbn
    book.category_id = int(category_id) if category_id else None
    book.publisher_id = int(publisher_id) if publisher_id else None
    book.available_quantity = available_quantity

    # Nếu model có total_quantity thì đảm bảo total_quantity không nhỏ hơn available_quantity.
    if hasattr(book, "total_quantity"):
        current_total = book.total_quantity or 0

        if current_total < available_quantity:
            book.total_quantity = available_quantity

    db.session.commit()

    flash("Cập nhật sách thành công.", "success")
    return admin_books_redirect()


# ================== DELETE BOOK ==================
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return admin_books_redirect()

    db.session.delete(book)
    db.session.commit()

    flash("Xóa sách thành công.", "success")
    return admin_books_redirect()