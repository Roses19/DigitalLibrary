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
def to_int_list(values):
    result = []

    for value in values:
        try:
            result.append(int(value))
        except (TypeError, ValueError):
            pass

    return result


def get_book_status_value(book):
    """
    Tình trạng sách được tự suy ra từ available_quantity.
    available_quantity > 0  => available
    available_quantity <= 0 => unavailable
    """
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
    """
    Tự đọc tình trạng từ danh sách sách đang có.
    Nếu kết quả chỉ có sách còn hàng thì chỉ hiện 'Còn sách'.
    Nếu kết quả chỉ có sách hết hàng thì chỉ hiện 'Đã hết'.
    """
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
    """
    Khi tìm ra sách, sidebar chỉ hiện:
    - Thể loại thuộc các sách đó
    - Nhà xuất bản thuộc các sách đó
    - Tình trạng thuộc các sách đó
    """
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
        categories = Category.query.filter(
            Category.id.in_(category_ids)
        ).order_by(Category.name.asc()).all()

    if publisher_ids:
        publishers = Publisher.query.filter(
            Publisher.id.in_(publisher_ids)
        ).order_by(Publisher.name.asc()).all()

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


def search_books():
    keyword = request.args.get("q", "").strip()

    selected_categories = request.args.getlist("category")
    selected_publishers = request.args.getlist("publisher")
    selected_statuses = request.args.getlist("status")

    # Chỉ khi bấm nút "Áp dụng bộ lọc" mới có filter=1
    filter_applied = request.args.get("filter") == "1"

    searched = bool(
        keyword or selected_categories or selected_publishers or selected_statuses
    )

    # Tìm sách theo keyword trước
    if keyword:
        matched_books = build_book_query(
            keyword=keyword
        ).order_by(Book.created_at.desc()).all()
    else:
        matched_books = []

    # Nếu có keyword, filter sidebar chỉ lấy thông tin của sách tìm được
    if keyword:
        categories, publishers, status_options = get_filter_options_from_books(matched_books)

        # Lần đầu tìm kiếm:
        # Tự tick thể loại, NXB, tình trạng theo sách trả về
        if not filter_applied:
            selected_categories = [str(category.id) for category in categories]
            selected_publishers = [str(publisher.id) for publisher in publishers]
            selected_statuses = [status["value"] for status in status_options]

    # Nếu không có keyword, hiện full filter
    else:
        categories = Category.query.order_by(Category.name.asc()).all()
        publishers = Publisher.query.order_by(Publisher.name.asc()).all()

        all_books = Book.query.all()
        status_options = get_status_options_from_books(all_books)

    # Danh sách sách hiển thị
    if searched:
        if keyword and not filter_applied:
            # Lần đầu search keyword thì hiển thị kết quả keyword
            books = matched_books
        else:
            # Khi bấm áp dụng bộ lọc
            books = build_book_query(
                keyword=keyword,
                category_ids=selected_categories,
                publisher_ids=selected_publishers,
                statuses=selected_statuses
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
        status_options=status_options,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_statuses=selected_statuses
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
        selected_statuses=selected_statuses
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

    book.quantity = int(quantity)

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