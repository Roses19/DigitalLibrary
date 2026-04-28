from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, session, request
from sqlalchemy.orm import joinedload

from ThuVienSo import db
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem


# ================== HELPER ==================
def get_current_user():
    """
    Lấy user đang đăng nhập.
    Ưu tiên user_id. Nếu session cũ chưa có user_id thì fallback theo username.
    """
    user_id = session.get("user_id")

    if user_id:
        return User.query.get(user_id)

    username = session.get("username")

    if username:
        return User.query.filter_by(username=username).first()

    return None


def safe_int(value, default=1):
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_role_name(role_name):
    return (role_name or "").strip().lower()


def is_admin_or_librarian():
    """
    Cho phép:
    - admin
    - quản trị
    - quản trị viên
    - thủ thư
    - librarian
    """
    current_user = get_current_user()

    if not current_user:
        return False

    if current_user.status != "active":
        return False

    role_name = normalize_role_name(current_user.role.name if current_user.role else "")

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


def get_admin_borrow_url(status=None, view=None):
    if view:
        return f"/admin?tab=borrow&view={view}"

    if status:
        return f"/admin?tab=borrow&status={status}"

    return "/admin?tab=borrow"


def get_next_url(default="/admin?tab=borrow"):
    return request.form.get("next_url") or request.args.get("next_url") or default


def get_request_status_label(status):
    labels = {
        "pending": "Chờ duyệt",
        "approved": "Đã duyệt",
        "rejected": "Đã từ chối",
    }

    return labels.get(status, status)


def get_record_status_label(status):
    labels = {
        "borrowing": "Đang mượn",
        "returned": "Đã trả",
    }

    return labels.get(status, status)


# ================== BOOK QUANTITY HELPER ==================
def get_book_with_copies(book_id):
    """
    Lấy sách kèm các bản lưu trữ ở chi nhánh.
    joinedload thêm branch để template lấy copy.branch.name.
    """
    return (
        Book.query
        .options(
            joinedload(Book.copies).joinedload(BookCopy.branch)
        )
        .get(book_id)
    )


def get_book_total_quantity(book):
    if not book or not getattr(book, "copies", None):
        return 0

    return sum(
        (copy.total_quantity or 0)
        for copy in book.copies
    )


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


def get_available_copies(book):
    """
    Lấy danh sách chi nhánh còn sách.
    Query trực tiếp từ BookCopy để tránh lỗi book.copies chưa load đủ dữ liệu.
    """
    if not book:
        return []

    return (
        BookCopy.query
        .options(joinedload(BookCopy.branch))
        .filter(
            BookCopy.book_id == book.id,
            BookCopy.available_quantity > 0
        )
        .order_by(BookCopy.branch_id.asc())
        .all()
    )


def get_copy_by_branch(book, branch_id):
    """
    Lấy BookCopy theo sách + chi nhánh.
    """
    branch_id = safe_int(branch_id, 0)

    if branch_id <= 0:
        return None

    if not book:
        return None

    return (
        BookCopy.query
        .options(joinedload(BookCopy.branch))
        .filter(
            BookCopy.book_id == book.id,
            BookCopy.branch_id == branch_id
        )
        .first()
    )


def attach_book_quantity(book):
    """
    Gắn số lượng tạm để template có thể dùng book.available_quantity nếu cần.
    Đây chỉ là attribute trong request hiện tại, không phụ thuộc cột DB.
    """
    if not book:
        return None

    total_quantity = get_book_total_quantity(book)
    available_quantity = get_book_available_quantity(book)

    book.display_total_quantity = total_quantity
    book.display_available_quantity = available_quantity

    try:
        book.available_quantity = available_quantity
    except Exception:
        pass

    try:
        book.total_quantity = total_quantity
    except Exception:
        pass

    return book


def get_branch_id_from_request():
    """
    branch_id có thể đến từ:
    - query string: ?branch_id=...
    - hidden input trong form
    - select trong form
    """
    branch_id = request.form.get("branch_id") or request.args.get("branch_id")
    return safe_int(branch_id, 0)


def get_selected_book_copy_from_item(item):
    """
    Lấy BookCopy đã lưu trong BorrowRequestItem nếu có.
    Ưu tiên book_copy_id vì đây là khóa chính xác nhất.
    """
    if not item:
        return None

    if hasattr(item, "book_copy") and item.book_copy:
        return item.book_copy

    if hasattr(item, "book_copy_id") and item.book_copy_id:
        return (
            BookCopy.query
            .options(joinedload(BookCopy.branch))
            .get(item.book_copy_id)
        )

    if hasattr(item, "branch_id") and item.branch_id:
        return (
            BookCopy.query
            .options(joinedload(BookCopy.branch))
            .filter(
                BookCopy.book_id == item.book_id,
                BookCopy.branch_id == item.branch_id
            )
            .first()
        )

    return None


def get_selected_branch_id_from_item(item):
    """
    Lấy branch_id từ BorrowRequestItem.
    Ưu tiên book_copy_id vì đây là dữ liệu chính xác nhất.
    """
    selected_copy = get_selected_book_copy_from_item(item)

    if selected_copy:
        return selected_copy.branch_id

    if hasattr(item, "branch_id") and item.branch_id:
        return item.branch_id

    return None


def assign_branch_to_item(item, branch_id, selected_copy=None):
    """
    Lưu chi nhánh mượn vào BorrowRequestItem.
    Ưu tiên lưu book_copy_id vì BookCopy chứa đúng sách + chi nhánh + kệ + số lượng.
    """
    if not item:
        return

    if selected_copy and hasattr(item, "book_copy_id"):
        item.book_copy_id = selected_copy.id

    if hasattr(item, "branch_id"):
        item.branch_id = branch_id


def assign_branch_to_record_item(record_item, branch_id, selected_copy=None):
    """
    Lưu chi nhánh vào BorrowRecordItem sau khi duyệt phiếu.
    """
    if not record_item:
        return

    if selected_copy and hasattr(record_item, "book_copy_id"):
        record_item.book_copy_id = selected_copy.id

    if hasattr(record_item, "branch_id"):
        record_item.branch_id = branch_id


def get_borrow_item_branch_name(item):
    """
    Lấy tên chi nhánh của một dòng yêu cầu mượn.
    Hỗ trợ:
    - item.book_copy_id
    - item.branch_id
    """
    if not item:
        return "Chưa chọn chi nhánh"

    selected_copy = get_selected_book_copy_from_item(item)

    if selected_copy and selected_copy.branch:
        return selected_copy.branch.name

    return "Chưa chọn chi nhánh"


def get_record_item_branch_name(item):
    if not item:
        return "Chưa chọn chi nhánh"

    if hasattr(item, "book_copy") and item.book_copy and item.book_copy.branch:
        return item.book_copy.branch.name

    if hasattr(item, "book_copy_id") and item.book_copy_id:
        selected_copy = (
            BookCopy.query
            .options(joinedload(BookCopy.branch))
            .get(item.book_copy_id)
        )

        if selected_copy and selected_copy.branch:
            return selected_copy.branch.name

    return "Chưa chọn chi nhánh"


def validate_borrow_selection(book, branch_id, quantity):
    """
    Kiểm tra chi nhánh + số lượng mượn.
    """
    if not book:
        return None, "Không tìm thấy sách."

    branch_id = safe_int(branch_id, 0)
    quantity = safe_int(quantity, 1)

    if branch_id <= 0:
        return None, "Vui lòng chọn chi nhánh mượn sách."

    selected_copy = get_copy_by_branch(book, branch_id)

    if not selected_copy:
        return None, "Chi nhánh này không có sách."

    available_quantity = selected_copy.available_quantity or 0

    if available_quantity <= 0:
        return None, "Chi nhánh này hiện đã hết sách."

    if quantity <= 0:
        return None, "Số lượng mượn phải lớn hơn 0."

    if quantity > available_quantity:
        return None, f"Số lượng mượn không được vượt quá số sách còn tại chi nhánh này ({available_quantity})."

    return selected_copy, None


def decrease_book_copy_quantity(book, quantity, branch_id=None):
    """
    Khi duyệt phiếu mượn:
    - Nếu có branch_id: trừ đúng chi nhánh đã chọn.
    - Nếu không có branch_id: fallback trừ từ các chi nhánh còn sách.
    """
    if not book:
        return False

    quantity = safe_int(quantity, 0)

    if quantity <= 0:
        return False

    branch_id = safe_int(branch_id, 0)

    if branch_id > 0:
        selected_copy = get_copy_by_branch(book, branch_id)

        if not selected_copy:
            return False

        current_available = selected_copy.available_quantity or 0

        if current_available < quantity:
            return False

        selected_copy.available_quantity = current_available - quantity
        return True

    available_quantity = get_book_available_quantity(book)

    if available_quantity < quantity:
        return False

    remaining = quantity

    copies = sorted(
        list(book.copies or []),
        key=lambda copy: copy.id
    )

    for copy in copies:
        if remaining <= 0:
            break

        current_available = copy.available_quantity or 0

        if current_available <= 0:
            continue

        deduct_quantity = min(current_available, remaining)
        copy.available_quantity = current_available - deduct_quantity
        remaining -= deduct_quantity

    return remaining == 0


def increase_book_copy_quantity(book, quantity, branch_id=None):
    """
    Khi trả sách:
    - Nếu có branch_id: cộng lại đúng chi nhánh đã mượn.
    - Nếu không có branch_id: fallback cộng vào các chi nhánh còn thiếu.
    """
    if not book:
        return False

    quantity = safe_int(quantity, 0)

    if quantity <= 0:
        return False

    branch_id = safe_int(branch_id, 0)

    if branch_id > 0:
        selected_copy = get_copy_by_branch(book, branch_id)

        if not selected_copy:
            return False

        selected_copy.available_quantity = (selected_copy.available_quantity or 0) + quantity
        return True

    copies = sorted(
        list(book.copies or []),
        key=lambda copy: copy.id
    )

    if not copies:
        return False

    remaining = quantity

    for copy in copies:
        if remaining <= 0:
            break

        total_quantity = copy.total_quantity or 0
        available_quantity = copy.available_quantity or 0
        space = total_quantity - available_quantity

        if space <= 0:
            continue

        add_quantity = min(space, remaining)
        copy.available_quantity = available_quantity + add_quantity
        remaining -= add_quantity

    if remaining > 0 and copies:
        copies[0].available_quantity = (copies[0].available_quantity or 0) + remaining
        remaining = 0

    return remaining == 0


# ================== USER BORROW STATE ==================
def get_user_borrow_states():
    current_user = get_current_user()

    if not current_user:
        return {}

    borrow_items = (
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

    for item in borrow_items:
        if item.book_id not in states:
            states[item.book_id] = {
                "request_id": item.borrow_request_id,
                "status": item.borrow_request.status
            }

    return states


def get_user_borrow_state_for_book(book_id):
    current_user = get_current_user()

    if not current_user:
        return None

    borrow_item = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(
            BorrowRequest.user_id == current_user.id,
            BorrowRequestItem.book_id == book_id,
            BorrowRequest.status == "pending"
        )
        .order_by(BorrowRequest.created_at.desc())
        .first()
    )

    if not borrow_item:
        return None

    borrow_request = borrow_item.borrow_request

    return {
        "request_id": borrow_request.id,
        "status": borrow_request.status
    }


# ================== USER: FORM MƯỢN SÁCH ==================
def show_borrow_form(book_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để mượn sách.", "error")
        return redirect(url_for("auth.login"))

    book = get_book_with_copies(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect("/books/list")

    attach_book_quantity(book)

    total_available_quantity = get_book_available_quantity(book)
    available_copies = get_available_copies(book)

    if total_available_quantity <= 0:
        flash("Sách này hiện đã hết, không thể mượn.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    selected_branch_id = get_branch_id_from_request()

    pending_item = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(
            BorrowRequest.user_id == current_user.id,
            BorrowRequestItem.book_id == book.id,
            BorrowRequest.status == "pending"
        )
        .order_by(BorrowRequest.created_at.desc())
        .first()
    )

    if pending_item:
        existing_branch_id = get_selected_branch_id_from_item(pending_item)

        if selected_branch_id and existing_branch_id and selected_branch_id != existing_branch_id:
            flash(
                "Bạn không thể mượn cùng một sách ở 2 chi nhánh khác nhau. "
                "Nếu muốn đổi chi nhánh, vui lòng sửa phiếu mượn hiện có.",
                "warning"
            )
            existing_copy = get_copy_by_branch(book, existing_branch_id)
            requested_copy = get_copy_by_branch(book, selected_branch_id)

            return render_template(
                "borrow/branch_conflict.html",
                book=book,
                existing_branch_name=(
                    existing_copy.branch.name
                    if existing_copy and existing_copy.branch
                    else "chi nhánh khác"
                ),
                requested_branch_name=(
                    requested_copy.branch.name
                    if requested_copy and requested_copy.branch
                    else "chi nhánh đang chọn"
                ),
                edit_url=url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id),
                detail_url=url_for("book.detail", book_id=book.id),
            )

        if selected_branch_id and not existing_branch_id:
            return redirect(
                url_for(
                    "borrow.edit_form",
                    borrow_id=pending_item.borrow_request_id,
                    branch_id=selected_branch_id
                )
            )

        return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

    selected_copy = get_copy_by_branch(book, selected_branch_id)

    if selected_branch_id and not selected_copy:
        flash("Chi nhánh bạn chọn không hợp lệ.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    selected_available_quantity = (
        selected_copy.available_quantity
        if selected_copy
        else total_available_quantity
    )

    return render_template(
        "borrow/request.html",
        book=book,
        available_quantity=selected_available_quantity,
        total_available_quantity=total_available_quantity,
        available_copies=available_copies,
        selected_copy=selected_copy,
        selected_branch_id=selected_branch_id,
        edit_mode=False,
        form_action=url_for("borrow.request_borrow", book_id=book.id),
        quantity=1,
        note="",
        page_title="Phiếu yêu cầu mượn sách",
        submit_text="Gửi yêu cầu mượn"
    )


# ================== USER: GỬI YÊU CẦU MƯỢN ==================
def create_borrow_request(book_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để mượn sách.", "error")
        return redirect(url_for("auth.login"))

    book = get_book_with_copies(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect("/books/list")

    attach_book_quantity(book)

    total_available_quantity = get_book_available_quantity(book)

    if total_available_quantity <= 0:
        flash("Sách này hiện đã hết, không thể mượn.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    branch_id = get_branch_id_from_request()
    quantity = safe_int(request.form.get("quantity"), 1)
    note = request.form.get("note", "").strip()

    selected_copy, error_message = validate_borrow_selection(book, branch_id, quantity)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for("borrow.borrow_form", book_id=book.id))

    pending_item = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(
            BorrowRequest.user_id == current_user.id,
            BorrowRequestItem.book_id == book.id,
            BorrowRequest.status == "pending"
        )
        .order_by(BorrowRequest.created_at.desc())
        .first()
    )

    if pending_item:
        existing_branch_id = get_selected_branch_id_from_item(pending_item)

        if existing_branch_id and branch_id != existing_branch_id:
            flash(
                "Bạn đã có phiếu mượn đang chờ duyệt cho sách này ở chi nhánh khác. "
                "Nếu muốn đổi chi nhánh, vui lòng sửa phiếu mượn hiện có.",
                "warning"
            )
            return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

        flash("Bạn đã có phiếu mượn đang chờ duyệt cho sách này. Vui lòng sửa phiếu hiện có.", "warning")
        return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

    borrow_request = BorrowRequest(
        user_id=current_user.id,
        status="pending",
        note=note
    )

    db.session.add(borrow_request)
    db.session.flush()

    borrow_item = BorrowRequestItem(
        borrow_request_id=borrow_request.id,
        book_id=book.id,
        quantity=quantity
    )

    assign_branch_to_item(borrow_item, branch_id, selected_copy)

    db.session.add(borrow_item)
    db.session.commit()

    flash("Đã gửi yêu cầu mượn sách. Vui lòng chờ thủ thư duyệt.", "success")
    return redirect(url_for("borrow.history"))


# ================== USER: LỊCH SỬ MƯỢN ==================
def get_borrow_history():
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để xem lịch sử mượn sách.", "error")
        return redirect(url_for("auth.login"))

    borrow_requests = (
        BorrowRequest.query
        .filter(BorrowRequest.user_id == current_user.id)
        .order_by(BorrowRequest.created_at.desc())
        .all()
    )

    borrow_records = (
        BorrowRecord.query
        .filter(BorrowRecord.user_id == current_user.id)
        .order_by(BorrowRecord.borrow_date.desc())
        .all()
    )

    return render_template(
        "borrow/history.html",
        borrow_requests=borrow_requests,
        borrow_records=borrow_records,
        get_request_status_label=get_request_status_label,
        get_record_status_label=get_record_status_label,
        get_borrow_item_branch_name=get_borrow_item_branch_name,
        get_record_item_branch_name=get_record_item_branch_name,
    )


# ================== USER: FORM SỬA YÊU CẦU ==================
def show_edit_borrow_request_form(borrow_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để sửa yêu cầu mượn sách.", "error")
        return redirect(url_for("auth.login"))

    borrow_request = BorrowRequest.query.get(borrow_id)

    if not borrow_request:
        flash("Không tìm thấy yêu cầu mượn sách.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.user_id != current_user.id:
        flash("Bạn không có quyền sửa yêu cầu này.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.status != "pending":
        flash("Chỉ có thể sửa yêu cầu đang chờ duyệt.", "warning")
        return redirect(url_for("borrow.history"))

    if not borrow_request.items:
        flash("Yêu cầu mượn không có sách.", "error")
        return redirect(url_for("borrow.history"))

    item = borrow_request.items[0]
    book = get_book_with_copies(item.book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("borrow.history"))

    attach_book_quantity(book)

    total_available_quantity = get_book_available_quantity(book)
    available_copies = get_available_copies(book)

    branch_id_from_url = get_branch_id_from_request()
    existing_branch_id = get_selected_branch_id_from_item(item)

    if branch_id_from_url and existing_branch_id and branch_id_from_url != existing_branch_id:
        flash(
            "Phiếu này đang mượn ở chi nhánh khác. "
            "Nếu muốn đổi chi nhánh, hãy chọn lại trong form sửa phiếu và bấm Lưu thay đổi.",
            "warning"
        )
        selected_branch_id = existing_branch_id
    else:
        selected_branch_id = branch_id_from_url or existing_branch_id

    selected_copy = get_copy_by_branch(book, selected_branch_id)

    selected_available_quantity = (
        selected_copy.available_quantity
        if selected_copy
        else total_available_quantity
    )

    quantity_value = item.quantity if selected_copy else 1

    return render_template(
        "borrow/request.html",
        book=book,
        available_quantity=selected_available_quantity,
        total_available_quantity=total_available_quantity,
        available_copies=available_copies,
        selected_copy=selected_copy,
        selected_branch_id=selected_branch_id,
        edit_mode=True,
        borrow_request=borrow_request,
        item=item,
        form_action=url_for("borrow.update_request", borrow_id=borrow_request.id),
        quantity=quantity_value,
        note=borrow_request.note or "",
        page_title="Thông tin mượn sách",
        submit_text="Lưu thay đổi",
    )


# ================== USER: CẬP NHẬT YÊU CẦU ==================
def update_borrow_request(borrow_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để cập nhật yêu cầu mượn sách.", "error")
        return redirect(url_for("auth.login"))

    borrow_request = BorrowRequest.query.get(borrow_id)

    if not borrow_request:
        flash("Không tìm thấy yêu cầu mượn sách.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.user_id != current_user.id:
        flash("Bạn không có quyền cập nhật yêu cầu này.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.status != "pending":
        flash("Chỉ có thể cập nhật yêu cầu đang chờ duyệt.", "warning")
        return redirect(url_for("borrow.history"))

    if not borrow_request.items:
        flash("Yêu cầu mượn không có sách.", "error")
        return redirect(url_for("borrow.history"))

    item = borrow_request.items[0]
    book = get_book_with_copies(item.book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("borrow.history"))

    attach_book_quantity(book)

    branch_id = get_branch_id_from_request()
    quantity = safe_int(request.form.get("quantity"), 1)
    note = request.form.get("note", "").strip()

    selected_copy, error_message = validate_borrow_selection(book, branch_id, quantity)

    if error_message:
        flash(error_message, "error")
        return redirect(url_for("borrow.edit_form", borrow_id=borrow_request.id))

    item.quantity = quantity
    assign_branch_to_item(item, branch_id, selected_copy)

    borrow_request.note = note

    db.session.commit()

    flash("Đã cập nhật yêu cầu mượn sách.", "success")
    return redirect(url_for("borrow.history"))


# ================== USER: XÓA YÊU CẦU ==================
def delete_borrow_request(borrow_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để xóa yêu cầu mượn sách.", "error")
        return redirect(url_for("auth.login"))

    borrow_request = BorrowRequest.query.get(borrow_id)

    if not borrow_request:
        flash("Không tìm thấy yêu cầu mượn sách.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.user_id != current_user.id:
        flash("Bạn không có quyền xóa yêu cầu này.", "error")
        return redirect(url_for("borrow.history"))

    if borrow_request.status != "pending":
        flash("Chỉ có thể xóa yêu cầu đang chờ duyệt.", "warning")
        return redirect(url_for("borrow.history"))

    for item in borrow_request.items:
        db.session.delete(item)

    db.session.delete(borrow_request)
    db.session.commit()

    flash("Đã xóa yêu cầu mượn sách.", "success")
    return redirect(url_for("borrow.history"))


# ================== ADMIN: DANH SÁCH YÊU CẦU ==================
def get_admin_borrow_requests():
    if not is_admin_or_librarian():
        flash("Bạn không có quyền truy cập chức năng này.", "error")
        return redirect("/admin?tab=users")

    status = request.args.get("status", "").strip()

    query = BorrowRequest.query

    if status:
        query = query.filter(BorrowRequest.status == status)

    borrow_requests = (
        query
        .order_by(BorrowRequest.created_at.desc())
        .all()
    )

    return render_template(
        "admin/borrows/index.html",
        borrow_requests=borrow_requests,
        selected_status=status,
        selected_view="",
        get_request_status_label=get_request_status_label,
        get_borrow_item_branch_name=get_borrow_item_branch_name,
    )


# ================== ADMIN: DUYỆT YÊU CẦU ==================
def approve_borrow_request(borrow_id):
    next_url = get_next_url("/admin?tab=borrow")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền thực hiện thao tác này.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    borrow_request = BorrowRequest.query.get(borrow_id)

    if not borrow_request:
        flash("Không tìm thấy yêu cầu mượn sách.", "error")
        return redirect(next_url)

    if borrow_request.status != "pending":
        flash("Yêu cầu này không còn ở trạng thái chờ duyệt.", "warning")
        return redirect(next_url)

    if not borrow_request.items:
        flash("Yêu cầu mượn không có sách.", "error")
        return redirect(next_url)

    books_cache = {}
    copies_cache = {}

    for item in borrow_request.items:
        book = get_book_with_copies(item.book_id)

        if not book:
            flash("Có sách trong yêu cầu không tồn tại.", "error")
            return redirect(next_url)

        branch_id = get_selected_branch_id_from_item(item)
        selected_copy = get_copy_by_branch(book, branch_id)

        if not selected_copy:
            flash(f'Sách "{book.title}" chưa chọn chi nhánh mượn.', "error")
            return redirect(next_url)

        available_quantity = selected_copy.available_quantity or 0

        if available_quantity < item.quantity:
            flash(f'Sách "{book.title}" không đủ số lượng tại chi nhánh đã chọn.', "error")
            return redirect(next_url)

        books_cache[item.book_id] = book
        copies_cache[item.id] = selected_copy

    borrow_request.status = "approved"
    borrow_request.approved_by = current_user.id if current_user else None
    borrow_request.approved_at = datetime.utcnow()

    borrow_record = BorrowRecord(
        borrow_request_id=borrow_request.id,
        user_id=borrow_request.user_id,
        borrow_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=14),
        status="borrowing",
        created_by=current_user.id if current_user else None,
    )

    db.session.add(borrow_record)
    db.session.flush()

    for item in borrow_request.items:
        book = books_cache.get(item.book_id)
        selected_copy = copies_cache.get(item.id)
        branch_id = selected_copy.branch_id if selected_copy else None

        record_item = BorrowRecordItem(
            borrow_record_id=borrow_record.id,
            book_id=item.book_id,
            quantity=item.quantity,
            returned_quantity=0,
            item_status="borrowing",
        )

        assign_branch_to_record_item(record_item, branch_id, selected_copy)

        db.session.add(record_item)

        success = decrease_book_copy_quantity(book, item.quantity, branch_id)

        if not success:
            db.session.rollback()
            flash(f'Sách "{book.title}" không đủ số lượng để duyệt.', "error")
            return redirect(next_url)

    db.session.commit()

    flash("Đã duyệt yêu cầu mượn sách.", "success")
    return redirect(next_url)


# ================== ADMIN: TỪ CHỐI YÊU CẦU ==================
def reject_borrow_request(borrow_id):
    next_url = get_next_url("/admin?tab=borrow")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền thực hiện thao tác này.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    borrow_request = BorrowRequest.query.get(borrow_id)

    if not borrow_request:
        flash("Không tìm thấy yêu cầu mượn sách.", "error")
        return redirect(next_url)

    if borrow_request.status != "pending":
        flash("Yêu cầu này không còn ở trạng thái chờ duyệt.", "warning")
        return redirect(next_url)

    reject_reason = request.form.get("reject_reason", "").strip()

    if not reject_reason:
        flash("Vui lòng nhập lý do từ chối.", "error")
        return redirect(next_url)

    borrow_request.status = "rejected"
    borrow_request.reject_reason = reject_reason
    borrow_request.approved_by = current_user.id if current_user else None
    borrow_request.approved_at = datetime.utcnow()

    db.session.commit()

    flash("Đã từ chối yêu cầu mượn sách.", "success")
    return redirect(next_url)


# ================== ADMIN: DANH SÁCH PHIẾU MƯỢN ==================
def get_admin_borrow_records():
    if not is_admin_or_librarian():
        flash("Bạn không có quyền truy cập chức năng này.", "error")
        return redirect("/admin?tab=users")

    borrow_records = (
        BorrowRecord.query
        .order_by(BorrowRecord.borrow_date.desc())
        .all()
    )

    return render_template(
        "admin/borrows/records.html",
        borrow_records=borrow_records,
        selected_view="records",
        get_record_status_label=get_record_status_label,
        get_record_item_branch_name=get_record_item_branch_name,
    )


# ================== ADMIN: XÁC NHẬN TRẢ SÁCH ==================
def return_borrow_record(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền thực hiện thao tác này.", "error")
        return redirect(next_url)

    borrow_record = BorrowRecord.query.get(record_id)

    if not borrow_record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    if borrow_record.status != "borrowing":
        flash("Phiếu mượn này không còn ở trạng thái đang mượn.", "warning")
        return redirect(next_url)

    for item in borrow_record.items:
        book = get_book_with_copies(item.book_id)
        not_returned_quantity = item.quantity - (item.returned_quantity or 0)

        if not book:
            continue

        branch_id = None

        if hasattr(item, "book_copy") and item.book_copy:
            branch_id = item.book_copy.branch_id
        elif hasattr(item, "book_copy_id") and item.book_copy_id:
            selected_copy = BookCopy.query.get(item.book_copy_id)

            if selected_copy:
                branch_id = selected_copy.branch_id
        elif hasattr(item, "branch_id") and item.branch_id:
            branch_id = item.branch_id

        if not_returned_quantity > 0:
            increase_book_copy_quantity(book, not_returned_quantity, branch_id)
            item.returned_quantity = item.quantity
            item.item_status = "returned"

    borrow_record.status = "returned"

    db.session.commit()

    flash("Đã xác nhận trả sách.", "success")
    return redirect(next_url)
