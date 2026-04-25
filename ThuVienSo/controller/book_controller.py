from flask import render_template, request, redirect, url_for, flash, session
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from ThuVienSo import db
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.author import Author
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
from ThuVienSo.data.models.branch import Branch


# =========================================================
# HELPER
# =========================================================
def get_current_user():
    user_id = session.get("user_id")

    if user_id:
        return User.query.get(user_id)

    username = session.get("username")

    if username:
        return User.query.filter_by(username=username).first()

    return None


def safe_int(value, default=None):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def get_book_available_quantity(book):
    """
    Tổng số lượng còn của sách ở tất cả chi nhánh.
    """
    if not book or not getattr(book, "copies", None):
        return 0

    return sum(
        (copy.available_quantity or 0)
        for copy in book.copies
    )


def get_book_total_quantity(book):
    """
    Tổng số lượng sách ở tất cả chi nhánh.
    """
    if not book or not getattr(book, "copies", None):
        return 0

    return sum(
        (copy.total_quantity or 0)
        for copy in book.copies
    )


def attach_book_quantity(book):
    """
    Gắn quantity tạm vào object Book để template dùng được:
    - book.available_quantity
    - book.total_quantity
    - book.display_available_quantity
    - book.display_total_quantity
    """
    if not book:
        return None

    available_quantity = get_book_available_quantity(book)
    total_quantity = get_book_total_quantity(book)

    book.display_available_quantity = available_quantity
    book.display_total_quantity = total_quantity

    try:
        book.available_quantity = available_quantity
    except Exception:
        pass

    try:
        book.total_quantity = total_quantity
    except Exception:
        pass

    return book


def attach_books_quantity(books):
    for book in books:
        attach_book_quantity(book)

    return books


def get_user_borrow_states():
    """
    Dùng cho book_card.html.
    Nếu có phiếu pending thì trả về request_id để cho phép sửa phiếu mượn.
    """
    current_user = get_current_user()

    if not current_user:
        return {}

    pending_items = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(
            BorrowRequest.user_id == current_user.id,
            BorrowRequest.status == "pending"
        )
        .order_by(BorrowRequest.created_at.desc())
        .all()
    )

    states = {}

    for item in pending_items:
        if item.book_id not in states:
            states[item.book_id] = {
                "status": "pending",
                "request_id": item.borrow_request_id
            }

    return states


def base_book_query():
    """
    Query sách kèm thông tin liên quan.
    """
    return (
        Book.query
        .options(
            joinedload(Book.authors),
            joinedload(Book.category),
            joinedload(Book.publisher),
            joinedload(Book.copies).joinedload(BookCopy.branch),
        )
    )


def get_dropdown_data():
    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()
    branches = Branch.query.order_by(Branch.name.asc()).all()

    return categories, publishers, branches


def render_book_list(
    books,
    page_title="Danh sách Sách",
    keyword="",
    category_id=None,
    publisher_id=None,
    branch_id=None,
    status="",
    is_advanced_empty=False,
):
    """
    Render chung cho list/search/advanced search.
    """
    categories, publishers, branches = get_dropdown_data()

    return render_template(
        "books/list.html",
        books=books,
        categories=categories,
        publishers=publishers,
        branches=branches,
        keyword=keyword,
        selected_category_id=category_id,
        selected_publisher_id=publisher_id,
        selected_branch_id=branch_id,
        selected_status=status,
        user_borrow_states=get_user_borrow_states(),
        show_filters=True,
        show_advanced=True,
        page_title=page_title,
        is_advanced_empty=is_advanced_empty,
    )


def apply_book_filters(query, keyword="", category_id=None, publisher_id=None, branch_id=None):
    """
    Apply lọc chung cho search và advanced search.
    """
    if keyword:
        search_text = f"%{keyword}%"

        query = (
            query
            .outerjoin(Book.authors)
            .outerjoin(Book.category)
            .outerjoin(Book.publisher)
            .filter(
                or_(
                    Book.title.ilike(search_text),
                    Book.isbn.ilike(search_text),
                    Author.name.ilike(search_text),
                    Category.name.ilike(search_text),
                    Publisher.name.ilike(search_text),
                )
            )
        )

    if category_id:
        query = query.filter(Book.category_id == category_id)

    if publisher_id:
        query = query.filter(Book.publisher_id == publisher_id)

    if branch_id:
        query = query.join(Book.copies).filter(BookCopy.branch_id == branch_id)

    return query


def filter_books_by_status(books, status):
    """
    Lọc tình trạng còn/hết sau khi đã attach quantity.
    """
    if status == "available":
        return [
            book for book in books
            if (book.available_quantity or 0) > 0
        ]

    if status == "unavailable":
        return [
            book for book in books
            if (book.available_quantity or 0) <= 0
        ]

    return books


# =========================================================
# HOME
# =========================================================
def get_home_books():
    """
    Trả về danh sách sách nổi bật cho trang chủ.
    KHÔNG render_template ở đây vì home_routes.py mới là nơi render trang chủ.
    """
    books = (
        base_book_query()
        .order_by(Book.id.asc())
        .limit(4)
        .all()
    )

    attach_books_quantity(books)

    return books


# =========================================================
# BOOK LIST
# =========================================================
def get_book_list():
    """
    Danh sách tất cả sách.
    """
    books = (
        base_book_query()
        .order_by(Book.id.asc())
        .all()
    )

    attach_books_quantity(books)

    return render_book_list(
        books=books,
        page_title="Danh sách Sách",
        keyword="",
        category_id=None,
        publisher_id=None,
        branch_id=None,
        status="",
        is_advanced_empty=False,
    )


# =========================================================
# SEARCH BOOKS
# =========================================================
def search_books():
    """
    Tìm kiếm cơ bản.
    Hỗ trợ cả keyword và q.
    Có truyền đủ bộ lọc sang list.html.
    """
    keyword = request.args.get("keyword", "").strip()
    q = request.args.get("q", "").strip()

    if not keyword and q:
        keyword = q

    category_id = safe_int(request.args.get("category_id"))
    publisher_id = safe_int(request.args.get("publisher_id"))
    branch_id = safe_int(request.args.get("branch_id"))
    status = request.args.get("status", "").strip()

    query = apply_book_filters(
        base_book_query(),
        keyword=keyword,
        category_id=category_id,
        publisher_id=publisher_id,
        branch_id=branch_id,
    )

    books = (
        query
        .order_by(Book.id.asc())
        .distinct()
        .all()
    )

    attach_books_quantity(books)
    books = filter_books_by_status(books, status)

    return render_book_list(
        books=books,
        page_title="Kết quả tìm kiếm",
        keyword=keyword,
        category_id=category_id,
        publisher_id=publisher_id,
        branch_id=branch_id,
        status=status,
        is_advanced_empty=False,
    )


# =========================================================
# ADVANCED SEARCH
# =========================================================
def advanced_search_controller():
    """
    Tìm kiếm nâng cao.
    Nếu chưa nhập điều kiện thì không load toàn bộ sách.
    """
    keyword = request.args.get("keyword", "").strip()
    q = request.args.get("q", "").strip()

    if not keyword and q:
        keyword = q

    category_id = safe_int(request.args.get("category_id"))
    publisher_id = safe_int(request.args.get("publisher_id"))
    branch_id = safe_int(request.args.get("branch_id"))
    status = request.args.get("status", "").strip()

    has_filter = bool(
        keyword
        or category_id
        or publisher_id
        or branch_id
        or status
    )

    if not has_filter:
        return render_book_list(
            books=[],
            page_title="Tìm kiếm nâng cao",
            keyword=keyword,
            category_id=category_id,
            publisher_id=publisher_id,
            branch_id=branch_id,
            status=status,
            is_advanced_empty=True,
        )

    query = apply_book_filters(
        base_book_query(),
        keyword=keyword,
        category_id=category_id,
        publisher_id=publisher_id,
        branch_id=branch_id,
    )

    books = (
        query
        .order_by(Book.id.asc())
        .distinct()
        .all()
    )

    attach_books_quantity(books)
    books = filter_books_by_status(books, status)

    return render_book_list(
        books=books,
        page_title="Tìm kiếm nâng cao",
        keyword=keyword,
        category_id=category_id,
        publisher_id=publisher_id,
        branch_id=branch_id,
        status=status,
        is_advanced_empty=False,
    )


# =========================================================
# BOOK DETAIL
# =========================================================
def get_book_detail(book_id):
    """
    Chi tiết sách.
    Trang detail.html của bạn đang dùng:
    - book.copies
    - copy.branch
    - available
    - total
    """
    book = (
        base_book_query()
        .filter(Book.id == book_id)
        .first()
    )

    if not book:
        return render_template(
            "books/detail.html",
            book=None
        )

    attach_book_quantity(book)

    available = book.available_quantity or 0
    total = book.total_quantity or 0

    return render_template(
        "books/detail.html",
        book=book,
        available=available,
        total=total,
        user_borrow_states=get_user_borrow_states()
    )


# =========================================================
# ADMIN BOOK LIST
# =========================================================
def get_admin_book_list():
    books = (
        base_book_query()
        .order_by(Book.id.asc())
        .all()
    )

    attach_books_quantity(books)

    categories, publishers, branches = get_dropdown_data()

    return render_template(
        "admin/books/index.html",
        books=books,
        categories=categories,
        publishers=publishers,
        branches=branches
    )


# =========================================================
# CREATE BOOK
# =========================================================
def create_book():
    """
    Thêm sách cơ bản.
    Hỗ trợ form có các field:
    title, isbn, pages, publish_year, language,
    description, cover_image, category_id, publisher_id
    """
    title = request.form.get("title", "").strip()

    if not title:
        flash("Tên sách không được để trống.", "error")
        return redirect(url_for("book.book_list"))

    isbn = request.form.get("isbn", "").strip()
    pages = safe_int(request.form.get("pages"))
    publish_year = safe_int(request.form.get("publish_year"))
    language = request.form.get("language", "").strip()
    description = request.form.get("description", "").strip()
    cover_image = request.form.get("cover_image", "").strip()
    category_id = safe_int(request.form.get("category_id"))
    publisher_id = safe_int(request.form.get("publisher_id"))

    book = Book(
        title=title,
        isbn=isbn or None,
        pages=pages,
        publish_year=publish_year,
        language=language or None,
        description=description or None,
        cover_image=cover_image or None,
        category_id=category_id,
        publisher_id=publisher_id
    )

    db.session.add(book)
    db.session.commit()

    flash("Đã thêm sách mới.", "success")
    return redirect(url_for("book.detail", book_id=book.id))


# =========================================================
# UPDATE BOOK
# =========================================================
def update_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách cần cập nhật.", "error")
        return redirect(url_for("book.book_list"))

    title = request.form.get("title", "").strip()

    if not title:
        flash("Tên sách không được để trống.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    book.title = title
    book.isbn = request.form.get("isbn", "").strip() or None
    book.pages = safe_int(request.form.get("pages"))
    book.publish_year = safe_int(request.form.get("publish_year"))
    book.language = request.form.get("language", "").strip() or None
    book.description = request.form.get("description", "").strip() or None
    book.cover_image = request.form.get("cover_image", "").strip() or None
    book.category_id = safe_int(request.form.get("category_id"))
    book.publisher_id = safe_int(request.form.get("publisher_id"))

    db.session.commit()

    flash("Đã cập nhật thông tin sách.", "success")
    return redirect(url_for("book.detail", book_id=book.id))


# =========================================================
# DELETE BOOK
# =========================================================
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách cần xóa.", "error")
        return redirect(url_for("book.book_list"))

    db.session.delete(book)
    db.session.commit()

    flash("Đã xóa sách.", "success")
    return redirect(url_for("book.book_list"))


# =========================================================
# CATEGORY LIST
# =========================================================
def get_categories():
    categories = Category.query.order_by(Category.id.asc()).all()

    return render_template(
        "books/categories.html",
        categories=categories
    )


# =========================================================
# CREATE CATEGORY
# =========================================================
def create_category():
    name = request.form.get("name", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    existed = Category.query.filter(Category.name == name).first()

    if existed:
        flash("Danh mục này đã tồn tại.", "warning")
        return redirect(url_for("book.categories"))

    category = Category(name=name)

    db.session.add(category)
    db.session.commit()

    flash("Đã thêm danh mục.", "success")
    return redirect(url_for("book.categories"))


# =========================================================
# UPDATE CATEGORY
# =========================================================
def update_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    name = request.form.get("name", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    category.name = name

    db.session.commit()

    flash("Đã cập nhật danh mục.", "success")
    return redirect(url_for("book.categories"))


# =========================================================
# DELETE CATEGORY
# =========================================================
def delete_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    db.session.delete(category)
    db.session.commit()

    flash("Đã xóa danh mục.", "success")
    return redirect(url_for("book.categories"))


# =========================================================
# BOOK COPY / CHI NHÁNH LƯU TRỮ
# =========================================================
def create_book_copy(book_id):
    """
    Thêm thông tin lưu trữ sách tại một chi nhánh.
    Form cần có:
    - branch_id
    - shelf_location
    - total_quantity
    - available_quantity
    """
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("book.book_list"))

    branch_id = safe_int(request.form.get("branch_id"))
    shelf_location = request.form.get("shelf_location", "").strip()
    total_quantity = safe_int(request.form.get("total_quantity"), 0)
    available_quantity = safe_int(request.form.get("available_quantity"), 0)

    if not branch_id:
        flash("Vui lòng chọn chi nhánh.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    if total_quantity < 0 or available_quantity < 0:
        flash("Số lượng không được nhỏ hơn 0.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    if available_quantity > total_quantity:
        flash("Số lượng còn không được lớn hơn tổng số lượng.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    existed_copy = BookCopy.query.filter_by(
        book_id=book.id,
        branch_id=branch_id
    ).first()

    if existed_copy:
        flash("Sách này đã có thông tin lưu trữ ở chi nhánh đã chọn.", "warning")
        return redirect(url_for("book.detail", book_id=book.id))

    book_copy = BookCopy(
        book_id=book.id,
        branch_id=branch_id,
        shelf_location=shelf_location or None,
        total_quantity=total_quantity,
        available_quantity=available_quantity
    )

    db.session.add(book_copy)
    db.session.commit()

    flash("Đã thêm thông tin lưu trữ sách.", "success")
    return redirect(url_for("book.detail", book_id=book.id))


def update_book_copy(copy_id):
    """
    Cập nhật thông tin lưu trữ sách theo chi nhánh.
    """
    book_copy = BookCopy.query.get(copy_id)

    if not book_copy:
        flash("Không tìm thấy thông tin lưu trữ cần cập nhật.", "error")
        return redirect(url_for("book.book_list"))

    book_id = book_copy.book_id

    branch_id = safe_int(request.form.get("branch_id"), book_copy.branch_id)
    shelf_location = request.form.get("shelf_location", "").strip()
    total_quantity = safe_int(request.form.get("total_quantity"), book_copy.total_quantity or 0)
    available_quantity = safe_int(request.form.get("available_quantity"), book_copy.available_quantity or 0)

    if not branch_id:
        flash("Vui lòng chọn chi nhánh.", "error")
        return redirect(url_for("book.detail", book_id=book_id))

    if total_quantity < 0 or available_quantity < 0:
        flash("Số lượng không được nhỏ hơn 0.", "error")
        return redirect(url_for("book.detail", book_id=book_id))

    if available_quantity > total_quantity:
        flash("Số lượng còn không được lớn hơn tổng số lượng.", "error")
        return redirect(url_for("book.detail", book_id=book_id))

    existed_copy = BookCopy.query.filter(
        BookCopy.book_id == book_id,
        BookCopy.branch_id == branch_id,
        BookCopy.id != book_copy.id
    ).first()

    if existed_copy:
        flash("Chi nhánh này đã có thông tin lưu trữ cho sách hiện tại.", "warning")
        return redirect(url_for("book.detail", book_id=book_id))

    book_copy.branch_id = branch_id
    book_copy.shelf_location = shelf_location or None
    book_copy.total_quantity = total_quantity
    book_copy.available_quantity = available_quantity

    db.session.commit()

    flash("Đã cập nhật thông tin lưu trữ sách.", "success")
    return redirect(url_for("book.detail", book_id=book_id))


def delete_book_copy(copy_id):
    """
    Xóa thông tin lưu trữ sách ở một chi nhánh.
    """
    book_copy = BookCopy.query.get(copy_id)

    if not book_copy:
        flash("Không tìm thấy thông tin lưu trữ cần xóa.", "error")
        return redirect(url_for("book.book_list"))

    book_id = book_copy.book_id

    db.session.delete(book_copy)
    db.session.commit()

    flash("Đã xóa thông tin lưu trữ sách.", "success")
    return redirect(url_for("book.detail", book_id=book_id))