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


def to_int_list(values):
    result = []

    for value in values:
        try:
            if value not in (None, ""):
                result.append(int(value))
        except (TypeError, ValueError):
            pass

    return result


def merge_selected_values(*values_groups):
    merged = []

    for values in values_groups:
        for value in values or []:
            if value not in (None, "") and value not in merged:
                merged.append(value)

    return merged


def get_book_status_value(book):
    available_quantity = getattr(book, "available_quantity", 0) or 0
    return "available" if available_quantity > 0 else "unavailable"


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
                "label": get_status_label(status_value),
            })

    status_options.sort(key=lambda item: 0 if item["value"] == "available" else 1)
    return status_options


def get_filter_options_from_books(books):
    category_ids = []
    publisher_ids = []
    branch_ids = []

    for book in books:
        if book.category_id and book.category_id not in category_ids:
            category_ids.append(book.category_id)

        if book.publisher_id and book.publisher_id not in publisher_ids:
            publisher_ids.append(book.publisher_id)

        for copy in getattr(book, "copies", []) or []:
            if copy.branch_id and copy.branch_id not in branch_ids:
                branch_ids.append(copy.branch_id)

    categories = []
    publishers = []
    branches = []

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

    if branch_ids:
        branches = (
            Branch.query
            .filter(Branch.id.in_(branch_ids))
            .order_by(Branch.name.asc())
            .all()
        )

    return categories, publishers, branches, get_status_options_from_books(books)


def apply_book_filters(query, keyword="", category_ids=None, publisher_ids=None, branch_ids=None):
    category_ids = to_int_list(category_ids or [])
    publisher_ids = to_int_list(publisher_ids or [])
    branch_ids = to_int_list(branch_ids or [])

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

    if category_ids:
        query = query.filter(Book.category_id.in_(category_ids))

    if publisher_ids:
        query = query.filter(Book.publisher_id.in_(publisher_ids))

    if branch_ids:
        query = query.join(Book.copies).filter(BookCopy.branch_id.in_(branch_ids))

    return query


def filter_books_by_status(books, statuses):
    statuses = set(statuses or [])

    if not statuses or {"available", "unavailable"}.issubset(statuses):
        return books

    if "available" in statuses:
        return [
            book for book in books
            if (book.available_quantity or 0) > 0
        ]

    if "unavailable" in statuses:
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

    return render_template(
        "books/list.html",
        books=books,
        user_borrow_states=get_user_borrow_states(),
    )


# =========================================================
# SEARCH BOOKS
# =========================================================
def search_books():
    keyword = request.args.get("keyword", "").strip()
    q = request.args.get("q", "").strip()

    if not keyword and q:
        keyword = q

    selected_categories = merge_selected_values(
        request.args.getlist("category"),
        request.args.getlist("category_id"),
    )
    selected_publishers = merge_selected_values(
        request.args.getlist("publisher"),
        request.args.getlist("publisher_id"),
    )
    selected_branches = merge_selected_values(
        request.args.getlist("branch"),
        request.args.getlist("branch_id"),
    )
    selected_statuses = merge_selected_values(
        request.args.getlist("status"),
    )

    filter_applied = request.args.get("filter") == "1"
    searched = bool(
        keyword
        or selected_categories
        or selected_publishers
        or selected_branches
        or selected_statuses
    )

    matched_books = []

    if keyword:
        matched_books = (
            apply_book_filters(base_book_query(), keyword=keyword)
            .order_by(Book.id.asc())
            .distinct()
            .all()
        )
        attach_books_quantity(matched_books)

    if keyword:
        categories, publishers, branches, status_options = get_filter_options_from_books(matched_books)

        if not filter_applied:
            selected_categories = [str(category.id) for category in categories]
            selected_publishers = [str(publisher.id) for publisher in publishers]
            selected_branches = [str(branch.id) for branch in branches]
            selected_statuses = [status["value"] for status in status_options]
    else:
        categories, publishers, branches = get_dropdown_data()
        all_books = base_book_query().all()
        attach_books_quantity(all_books)
        status_options = get_status_options_from_books(all_books)

    if searched:
        if keyword and not filter_applied:
            books = matched_books
        else:
            books = (
                apply_book_filters(
                    base_book_query(),
                    keyword=keyword,
                    category_ids=selected_categories,
                    publisher_ids=selected_publishers,
                    branch_ids=selected_branches,
                )
                .order_by(Book.id.asc())
                .distinct()
                .all()
            )
            attach_books_quantity(books)
            books = filter_books_by_status(books, selected_statuses)
    else:
        books = []

    selected_branch_count = len(set(to_int_list(selected_branches)))
    all_branch_count = Branch.query.count()

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=searched,
        categories=categories,
        publishers=publishers,
        branches=branches,
        status_options=status_options,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_branches=selected_branches,
        selected_statuses=selected_statuses,
        branch_all_selected=bool(branches) and selected_branch_count == all_branch_count,
        user_borrow_states=get_user_borrow_states(),
    )


# =========================================================
# ADVANCED SEARCH
# =========================================================
def advanced_search_controller():
    return search_books()


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
    next_url = request.form.get("next_url")
    title = request.form.get("title", "").strip()

    if not title:
        flash("Tên sách không được để trống.", "error")
        return redirect(next_url or url_for("book.book_list"))

    isbn = request.form.get("isbn", "").strip()
    pages = safe_int(request.form.get("pages"))
    publish_year = safe_int(request.form.get("publish_year"))
    language = request.form.get("language", "").strip()
    description = request.form.get("description", "").strip()
    cover_image = request.form.get("cover_image", "").strip()
    category_id = safe_int(request.form.get("category_id"))
    publisher_id = safe_int(request.form.get("publisher_id"))
    branch_id = safe_int(request.form.get("branch_id"))
    shelf_location = request.form.get("shelf_location", "").strip()
    total_quantity = safe_int(request.form.get("total_quantity"), 0)
    available_quantity = safe_int(request.form.get("available_quantity"), 0)

    if total_quantity < 0 or available_quantity < 0:
        flash("Số lượng không được nhỏ hơn 0.", "error")
        return redirect(next_url or url_for("book.book_list"))

    if available_quantity > total_quantity:
        flash("Số lượng còn không được lớn hơn tổng số lượng.", "error")
        return redirect(next_url or url_for("book.book_list"))

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
    db.session.flush()

    if branch_id:
        db.session.add(
            BookCopy(
                book_id=book.id,
                branch_id=branch_id,
                shelf_location=shelf_location or None,
                total_quantity=total_quantity,
                available_quantity=available_quantity
            )
        )

    db.session.commit()

    flash("Đã thêm sách mới.", "success")
    return redirect(next_url or url_for("book.detail", book_id=book.id))


# =========================================================
# UPDATE BOOK
# =========================================================
def update_book(book_id):
    next_url = request.form.get("next_url") or url_for("book.detail", book_id=book_id)
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách cần cập nhật.", "error")
        return redirect(next_url)

    title = request.form.get("title", "").strip()

    if not title:
        flash("Tên sách không được để trống.", "error")
        return redirect(next_url)

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
    return redirect(next_url)


# =========================================================
# DELETE BOOK
# =========================================================
def delete_book(book_id):
    next_url = request.form.get("next_url") or url_for("book.book_list")
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách cần xóa.", "error")
        return redirect(next_url)

    db.session.delete(book)
    db.session.commit()

    flash("Đã xóa sách.", "success")
    return redirect(next_url)


# =========================================================
# CATEGORY LIST
# =========================================================
def get_categories():
    from sqlalchemy import func

    category_rows = (
        db.session.query(Category, func.count(Book.id))
        .outerjoin(Book, Book.category_id == Category.id)
        .group_by(Category.id)
        .order_by(Category.id.asc())
        .all()
    )

    categories = []

    for category, book_count in category_rows:
        category.book_count = book_count
        categories.append(category)

    return render_template(
        "books/categories.html",
        categories=categories,
        can_manage_categories=can_manage_categories()
    )


def get_branches():
    branches = (
        Branch.query
        .order_by(Branch.name.asc())
        .all()
    )

    for branch in branches:
        branch.book_count = len({copy.book_id for copy in branch.copies or []})
        branch.total_quantity = sum((copy.total_quantity or 0) for copy in branch.copies or [])
        branch.available_quantity = sum((copy.available_quantity or 0) for copy in branch.copies or [])

    return render_template(
        "books/branches.html",
        branches=branches,
    )


# =========================================================
# CREATE CATEGORY
# =========================================================
def create_category():
    name = request.form.get("name", "").strip()
    if not can_manage_categories():
        flash("Bạn không có quyền thêm danh mục.", "error")
        return redirect(url_for("book.categories"))

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
    if not can_manage_categories():
        flash("Bạn không có quyền sửa danh mục.", "error")
        return redirect(url_for("book.categories"))

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
    if not can_manage_categories():
        flash("Bạn không có quyền xóa danh mục.", "error")
        return redirect(url_for("book.categories"))

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
    next_url = request.form.get("next_url") or url_for("book.detail", book_id=book_id)
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect(next_url)

    branch_id = safe_int(request.form.get("branch_id"))
    shelf_location = request.form.get("shelf_location", "").strip()
    total_quantity = safe_int(request.form.get("total_quantity"), 0)
    available_quantity = safe_int(request.form.get("available_quantity"), 0)

    if not branch_id:
        flash("Vui lòng chọn chi nhánh.", "error")
        return redirect(next_url)

    if total_quantity < 0 or available_quantity < 0:
        flash("Số lượng không được nhỏ hơn 0.", "error")
        return redirect(next_url)

    if available_quantity > total_quantity:
        flash("Số lượng còn không được lớn hơn tổng số lượng.", "error")
        return redirect(next_url)

    existed_copy = BookCopy.query.filter_by(
        book_id=book.id,
        branch_id=branch_id
    ).first()

    if existed_copy:
        flash("Sách này đã có thông tin lưu trữ ở chi nhánh đã chọn.", "warning")
        return redirect(next_url)

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
    return redirect(next_url)


def update_book_copy(copy_id):
    """
    Cập nhật thông tin lưu trữ sách theo chi nhánh.
    """
    next_url = request.form.get("next_url")
    book_copy = BookCopy.query.get(copy_id)

    if not book_copy:
        flash("Không tìm thấy thông tin lưu trữ cần cập nhật.", "error")
        return redirect(next_url or url_for("book.book_list"))

    book_id = book_copy.book_id
    next_url = next_url or url_for("book.detail", book_id=book_id)

    branch_id = safe_int(request.form.get("branch_id"), book_copy.branch_id)
    shelf_location = request.form.get("shelf_location", "").strip()
    total_quantity = safe_int(request.form.get("total_quantity"), book_copy.total_quantity or 0)
    available_quantity = safe_int(request.form.get("available_quantity"), book_copy.available_quantity or 0)

    if not branch_id:
        flash("Vui lòng chọn chi nhánh.", "error")
        return redirect(next_url)

    if total_quantity < 0 or available_quantity < 0:
        flash("Số lượng không được nhỏ hơn 0.", "error")
        return redirect(next_url)

    if available_quantity > total_quantity:
        flash("Số lượng còn không được lớn hơn tổng số lượng.", "error")
        return redirect(next_url)

    existed_copy = BookCopy.query.filter(
        BookCopy.book_id == book_id,
        BookCopy.branch_id == branch_id,
        BookCopy.id != book_copy.id
    ).first()

    if existed_copy:
        flash("Chi nhánh này đã có thông tin lưu trữ cho sách hiện tại.", "warning")
        return redirect(next_url)

    book_copy.branch_id = branch_id
    book_copy.shelf_location = shelf_location or None
    book_copy.total_quantity = total_quantity
    book_copy.available_quantity = available_quantity

    db.session.commit()

    flash("Đã cập nhật thông tin lưu trữ sách.", "success")
    return redirect(next_url)


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
def can_manage_categories():
    current_user = get_current_user()

    if not current_user:
        return False

    role_name = ""
    if current_user.role:
        role_name = (current_user.role.name or "").strip().lower()

    allowed_roles = {
        "admin",
        "quản trị",
        "quan tri",
        "quản trị viên",
        "quan tri vien",
        "thủ thư",
        "thu thu",
        "librarian",
    }

    return role_name in allowed_roles