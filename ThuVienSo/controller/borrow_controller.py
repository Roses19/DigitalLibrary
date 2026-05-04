from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, session, request
from sqlalchemy.orm import joinedload
from sqlalchemy import text

from ThuVienSo import db
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem
from ThuVienSo.data.models.rule import LibraryRule

try:
    from ThuVienSo.data.models.return_record import ReturnRecord
except Exception:
    ReturnRecord = None


# ================== HELPER ==================
def get_current_user():
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
        "overdue": "Trễ hạn",
        "overdue_processed": "Đã xử lý trả trễ",
        "borrow_banned": "Cấm mượn",
    }

    return labels.get(status, status)


def get_active_rule():
    rule = (
        LibraryRule.query
        .filter_by(is_active=True)
        .order_by(LibraryRule.id.desc())
        .first()
    )

    if rule:
        return rule

    # Fallback không lưu DB, chỉ để code không lỗi nếu chưa có rule.
    rule = LibraryRule()
    rule.max_books_per_borrow = 3
    rule.max_borrow_days = 14

    if hasattr(rule, "max_extend_times"):
        rule.max_extend_times = 1

    return rule


def get_rule_max_books():
    rule = get_active_rule()
    return safe_int(getattr(rule, "max_books_per_borrow", 3), 3)


def get_rule_max_borrow_days():
    rule = get_active_rule()
    return safe_int(getattr(rule, "max_borrow_days", 14), 14)


def get_rule_max_extend_times():
    rule = get_active_rule()
    return safe_int(getattr(rule, "max_extend_times", 1), 1)


def get_borrow_ban_message(user):
    if not user:
        return None

    if getattr(user, "status", "") == "locked":
        return "Tài khoản của bạn đang bị cấm mượn sách. Vui lòng liên hệ thủ thư hoặc quản trị viên."

    if getattr(user, "status", "") == "inactive":
        return "Tài khoản của bạn đang ngừng hoạt động, không thể mượn sách."

    return None


def refresh_overdue_records(user_id=None):
    query = BorrowRecord.query.filter(
        BorrowRecord.status == "borrowing",
        BorrowRecord.due_date < datetime.utcnow(),
    )

    if user_id:
        query = query.filter(BorrowRecord.user_id == user_id)

    updated = query.update(
        {BorrowRecord.status: "overdue"},
        synchronize_session=False,
    )

    if updated:
        db.session.commit()

    return updated


def get_overdue_records(user_id):
    refresh_overdue_records(user_id)

    return (
        BorrowRecord.query
        .filter(
            BorrowRecord.user_id == user_id,
            BorrowRecord.status == "overdue",
        )
        .order_by(BorrowRecord.due_date.asc())
        .all()
    )


def get_active_borrow_quantity(user_id):
    records = (
        BorrowRecord.query
        .options(joinedload(BorrowRecord.items))
        .filter(
            BorrowRecord.user_id == user_id,
            BorrowRecord.status.in_(["borrowing", "overdue"]),
        )
        .all()
    )

    total = 0

    for record in records:
        for item in record.items:
            total += max((item.quantity or 0) - (item.returned_quantity or 0), 0)

    return total


def get_pending_borrow_quantity(user_id, excluded_request_id=None):
    requests = (
        BorrowRequest.query
        .options(joinedload(BorrowRequest.items))
        .filter(
            BorrowRequest.user_id == user_id,
            BorrowRequest.status == "pending",
        )
        .all()
    )

    total = 0

    for borrow_request in requests:
        if excluded_request_id and borrow_request.id == excluded_request_id:
            continue

        for item in borrow_request.items:
            total += item.quantity or 0

    return total


def get_borrow_limit_message(user_id, requested_quantity=0, excluded_request_id=None):
    max_books = get_rule_max_books()
    active_quantity = get_active_borrow_quantity(user_id)
    pending_quantity = get_pending_borrow_quantity(user_id, excluded_request_id)

    if active_quantity >= max_books:
        return "Bạn đã mượn tối đa số sách cho phép, vui lòng mượn lại sau khi đã trả bớt sách."

    if active_quantity + pending_quantity + requested_quantity > max_books:
        remaining = max(max_books - active_quantity - pending_quantity, 0)

        return (
            f"Bạn chỉ còn có thể mượn thêm {remaining} quyển theo quy định hiện tại. "
            "Vui lòng giảm số lượng hoặc mượn lại sau khi trả sách."
        )

    return None


def get_overdue_block_message(user_id):
    overdue_records = get_overdue_records(user_id)

    if overdue_records:
        return (
            "Tài khoản của bạn đang có sách trễ hạn trả. "
            "Vui lòng trả sách quá hạn trước khi gửi yêu cầu mượn mới."
        )

    return None


# ================== BOOK QUANTITY HELPER ==================
def get_book_with_copies(book_id):
    return (
        Book.query
        .options(joinedload(Book.copies).joinedload(BookCopy.branch))
        .get(book_id)
    )


def get_book_total_quantity(book):
    if not book or not getattr(book, "copies", None):
        return 0

    return sum((copy.total_quantity or 0) for copy in book.copies)


def get_book_available_quantity(book):
    if not book or not getattr(book, "copies", None):
        return 0

    return sum((copy.available_quantity or 0) for copy in book.copies)


def get_available_copies(book):
    if not book:
        return []

    return (
        BookCopy.query
        .options(joinedload(BookCopy.branch))
        .filter(
            BookCopy.book_id == book.id,
            BookCopy.available_quantity > 0,
        )
        .order_by(BookCopy.branch_id.asc())
        .all()
    )


def get_copy_by_branch(book, branch_id):
    branch_id = safe_int(branch_id, 0)

    if branch_id <= 0 or not book:
        return None

    return (
        BookCopy.query
        .options(joinedload(BookCopy.branch))
        .filter(
            BookCopy.book_id == book.id,
            BookCopy.branch_id == branch_id,
        )
        .first()
    )


def attach_book_quantity(book):
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
    branch_id = request.form.get("branch_id") or request.args.get("branch_id")
    return safe_int(branch_id, 0)


def get_selected_book_copy_from_item(item):
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
                BookCopy.branch_id == item.branch_id,
            )
            .first()
        )

    return None


def get_selected_branch_id_from_item(item):
    selected_copy = get_selected_book_copy_from_item(item)

    if selected_copy:
        return selected_copy.branch_id

    if hasattr(item, "branch_id") and item.branch_id:
        return item.branch_id

    return None


def assign_branch_to_item(item, branch_id, selected_copy=None):
    if not item:
        return

    if selected_copy and hasattr(item, "book_copy_id"):
        item.book_copy_id = selected_copy.id

    if hasattr(item, "branch_id"):
        item.branch_id = branch_id


def assign_branch_to_record_item(record_item, branch_id, selected_copy=None):
    if not record_item:
        return

    if selected_copy and hasattr(record_item, "book_copy_id"):
        record_item.book_copy_id = selected_copy.id

    if hasattr(record_item, "branch_id"):
        record_item.branch_id = branch_id


def get_borrow_item_branch_name(item):
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
    copies = sorted(list(book.copies or []), key=lambda copy: copy.id)

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

    copies = sorted(list(book.copies or []), key=lambda copy: copy.id)

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


def mark_record_items_returned(borrow_record):
    if not borrow_record:
        return

    for item in borrow_record.items:
        book = get_book_with_copies(item.book_id)

        if not book:
            continue

        not_returned_quantity = max(
            (item.quantity or 0) - (item.returned_quantity or 0),
            0,
        )

        if not_returned_quantity <= 0:
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

        increase_book_copy_quantity(book, not_returned_quantity, branch_id)

        item.returned_quantity = item.quantity
        item.item_status = "returned"


def add_return_record(borrow_record, current_user, note=None):
    if ReturnRecord is None or not borrow_record:
        return

    try:
        return_record = ReturnRecord(
            borrow_record_id=borrow_record.id,
            processed_by=current_user.id if current_user else None,
            return_date=datetime.utcnow(),
            note=note,
            created_at=datetime.utcnow(),
        )
        db.session.add(return_record)
    except TypeError:
        # Nếu model ReturnRecord của nhóm bạn khác field, bỏ qua để không làm lỗi chức năng chính.
        pass


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
            BorrowRequest.status == "pending",
        )
        .order_by(BorrowRequest.created_at.desc())
        .all()
    )

    states = {}

    for item in borrow_items:
        if item.book_id not in states:
            states[item.book_id] = {
                "request_id": item.borrow_request_id,
                "status": item.borrow_request.status,
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
            BorrowRequest.status == "pending",
        )
        .order_by(BorrowRequest.created_at.desc())
        .first()
    )

    if not borrow_item:
        return None

    borrow_request = borrow_item.borrow_request

    return {
        "request_id": borrow_request.id,
        "status": borrow_request.status,
    }


# ================== USER: FORM MƯỢN SÁCH ==================
def show_borrow_form(book_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để mượn sách.", "error")
        return redirect(url_for("auth.login"))

    ban_message = get_borrow_ban_message(current_user)
    if ban_message:
        flash(ban_message, "warning")
        return redirect(url_for("borrow.history"))

    overdue_message = get_overdue_block_message(current_user.id)
    if overdue_message:
        flash(overdue_message, "warning")
        return redirect(url_for("borrow.history"))

    limit_message = get_borrow_limit_message(current_user.id)
    if limit_message:
        flash(limit_message, "warning")
        return redirect(url_for("borrow.history"))

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
            BorrowRequest.status == "pending",
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
                "warning",
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
                    branch_id=selected_branch_id,
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
        submit_text="Gửi yêu cầu mượn",
    )


# ================== USER: GỬI YÊU CẦU MƯỢN ==================
def create_borrow_request(book_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để mượn sách.", "error")
        return redirect(url_for("auth.login"))

    ban_message = get_borrow_ban_message(current_user)
    if ban_message:
        flash(ban_message, "warning")
        return redirect(url_for("borrow.history"))

    overdue_message = get_overdue_block_message(current_user.id)
    if overdue_message:
        flash(overdue_message, "warning")
        return redirect(url_for("borrow.history"))

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

    limit_message = get_borrow_limit_message(current_user.id, requested_quantity=quantity)
    if limit_message:
        flash(limit_message, "warning")
        return redirect(url_for("borrow.history"))

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
            BorrowRequest.status == "pending",
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
                "warning",
            )
            return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

        flash("Bạn đã có phiếu mượn đang chờ duyệt cho sách này. Vui lòng sửa phiếu hiện có.", "warning")
        return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

    borrow_request = BorrowRequest(
        user_id=current_user.id,
        status="pending",
        note=note,
    )

    db.session.add(borrow_request)
    db.session.flush()

    borrow_item = BorrowRequestItem(
        borrow_request_id=borrow_request.id,
        book_id=book.id,
        quantity=quantity,
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

    refresh_overdue_records(current_user.id)
    rule = get_active_rule()

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
        rule=rule,
        now=datetime.utcnow(),
    )


borrow_history_controller = get_borrow_history


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
            "warning",
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

    limit_message = get_borrow_limit_message(
        current_user.id,
        requested_quantity=quantity,
        excluded_request_id=borrow_request.id,
    )
    if limit_message:
        flash(limit_message, "warning")
        return redirect(url_for("borrow.edit_form", borrow_id=borrow_request.id))

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


# ================== USER: GỬI YÊU CẦU GIA HẠN ==================
def request_borrow_extension(record_id):
    current_user = get_current_user()

    if not current_user:
        flash("Bạn cần đăng nhập để gửi yêu cầu gia hạn.", "error")
        return redirect(url_for("auth.login"))

    refresh_overdue_records(current_user.id)

    record = BorrowRecord.query.get(record_id)

    if not record or record.user_id != current_user.id:
        flash("Không tìm thấy phiếu mượn cần gia hạn.", "error")
        return redirect(url_for("borrow.history"))

    if record.status == "overdue":
        flash("Phiếu mượn đã trễ hạn, không thể gửi yêu cầu gia hạn.", "warning")
        return redirect(url_for("borrow.history"))

    if record.status != "borrowing":
        flash("Chỉ có thể gia hạn phiếu đang mượn.", "warning")
        return redirect(url_for("borrow.history"))

    if record.due_date and record.due_date < datetime.utcnow():
        record.status = "overdue"
        db.session.commit()
        flash("Phiếu mượn đã trễ hạn, không thể gửi yêu cầu gia hạn.", "warning")
        return redirect(url_for("borrow.history"))

    max_extend_times = 1
    extend_count = record.extend_count or 0
    extension_status = (record.extension_status or "").strip().lower()

    # Chỉ được gửi gia hạn 1 lần duy nhất.
    # pending: đang chờ duyệt
    # approved: đã được duyệt
    # rejected: đã bị từ chối
    if extension_status in {"pending", "approved", "rejected"} or extend_count >= max_extend_times:
        flash("Phiếu này đã sử dụng lượt gia hạn, không thể gửi gia hạn lại.", "warning")
        return redirect(url_for("borrow.history"))

    max_extend_days = get_rule_max_borrow_days()

    if request.method == "GET":
        return render_template(
            "borrow/extend.html",
            record=record,
            max_extend_days=max_extend_days,
            max_extend_times=max_extend_times,
            extend_count=extend_count,
        )

    extend_days = safe_int(request.form.get("extend_days"), 0)

    if extend_days <= 0:
        flash("Số ngày gia hạn không hợp lệ.", "error")
        return redirect(url_for("borrow.extend_record", record_id=record.id))

    if extend_days > max_extend_days:
        flash(
            f"Số ngày gia hạn không được vượt quá {max_extend_days} ngày theo quy định.",
            "error"
        )
        return redirect(url_for("borrow.extend_record", record_id=record.id))

    record.extension_status = "pending"
    record.extension_days = extend_days
    record.extension_requested_at = datetime.utcnow()

    db.session.commit()

    flash("Đã gửi yêu cầu gia hạn. Vui lòng chờ thủ thư/admin xác nhận.", "success")
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


# ================== ADMIN: DUYỆT YÊU CẦU MƯỢN ==================
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

    user = User.query.get(borrow_request.user_id)
    ban_message = get_borrow_ban_message(user)
    if ban_message:
        flash(ban_message, "warning")
        return redirect(next_url)

    refresh_overdue_records(borrow_request.user_id)

    overdue_message = get_overdue_block_message(borrow_request.user_id)
    if overdue_message:
        flash(overdue_message, "warning")
        return redirect(next_url)

    requested_quantity = sum((item.quantity or 0) for item in borrow_request.items)

    limit_message = get_borrow_limit_message(
        borrow_request.user_id,
        requested_quantity=requested_quantity,
        excluded_request_id=borrow_request.id,
    )
    if limit_message:
        flash(limit_message, "warning")
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
        due_date=datetime.utcnow() + timedelta(days=get_rule_max_borrow_days()),
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


# ================== ADMIN: TỪ CHỐI YÊU CẦU MƯỢN ==================
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

    refresh_overdue_records()

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


# ================== ADMIN/THỦ THƯ: TRA CỨU LỊCH SỬ MƯỢN ==================
def borrow_lookup_controller():
    if not is_admin_or_librarian():
        flash("Bạn không có quyền truy cập trang này.", "error")
        return redirect(url_for("home.index"))

    refresh_overdue_records()

    keyword = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    conditions = ["1=1"]
    params = {}

    if keyword:
        conditions.append("(u.username LIKE :kw OR u.full_name LIKE :kw)")
        params["kw"] = f"%{keyword}%"

    if status_filter:
        conditions.append("LOWER(TRIM(br.status)) = :status")
        params["status"] = status_filter.lower().strip()

    if from_date:
        conditions.append("DATE(br.borrow_date) >= :from_date")
        params["from_date"] = from_date

    if to_date:
        conditions.append("DATE(br.borrow_date) <= :to_date")
        params["to_date"] = to_date

    where = " AND ".join(conditions)

    sql = f"""
        SELECT
            br.id AS borrow_record_id,
            br.borrow_date,
            br.due_date,
            br.status AS borrow_status,
            u.id AS user_id,
            u.username,
            u.full_name,
            GROUP_CONCAT(b.title SEPARATOR ', ') AS book_titles,
            SUM(bri.quantity) AS total_quantity
        FROM borrow_records br
        JOIN users u ON br.user_id = u.id
        JOIN borrow_record_items bri ON br.id = bri.borrow_record_id
        JOIN books b ON bri.book_id = b.id
        WHERE {where}
        GROUP BY br.id, br.borrow_date, br.due_date, br.status, u.id, u.username, u.full_name
        ORDER BY br.borrow_date DESC
        LIMIT 200
    """

    records = db.session.execute(text(sql), params).mappings().all()

    return render_template(
        "borrow/lookup.html",
        records=records,
        keyword=keyword,
        status_filter=status_filter,
        from_date=from_date,
        to_date=to_date,
        now=datetime.now(),
    )


# ================== ADMIN/THỦ THƯ: QUẢN LÝ PHIẾU ĐANG MƯỢN ==================
def borrow_manage_controller():
    if not is_admin_or_librarian():
        flash("Bạn không có quyền truy cập trang này.", "error")
        return redirect(url_for("home.index"))

    refresh_overdue_records()

    active_records = (
        BorrowRecord.query
        .filter(BorrowRecord.status.in_(["borrowing", "overdue"]))
        .order_by(BorrowRecord.borrow_date.asc())
        .all()
    )

    returned_records = (
        BorrowRecord.query
        .filter(BorrowRecord.status.in_(["returned", "overdue_processed", "borrow_banned"]))
        .order_by(BorrowRecord.borrow_date.desc())
        .limit(50)
        .all()
    )

    return render_template(
        "borrow/manage.html",
        active_records=active_records,
        returned_records=returned_records,
        now=datetime.now(),
        get_record_status_label=get_record_status_label,
        get_record_item_branch_name=get_record_item_branch_name,
    )


# ================== ADMIN: XÁC NHẬN TRẢ SÁCH ==================
def return_borrow_record(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền thực hiện thao tác này.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    borrow_record = BorrowRecord.query.get(record_id)

    if not borrow_record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    if borrow_record.status != "borrowing":
        flash("Chỉ xác nhận trả cho phiếu đang mượn. Phiếu trễ hạn cần xử lý bằng Cho phép mượn lại hoặc Cấm mượn.", "warning")
        return redirect(next_url)

    mark_record_items_returned(borrow_record)

    borrow_record.status = "returned"

    if getattr(borrow_record, "extension_status", None) == "pending":
        borrow_record.extension_status = "rejected"

    note = request.form.get("note", "").strip()
    add_return_record(
        borrow_record,
        current_user,
        note=note if note else None,
    )

    db.session.commit()

    flash("Đã xác nhận trả sách.", "success")
    return redirect(next_url)


return_book_controller = return_borrow_record


# ================== ADMIN: XÁC NHẬN / TỪ CHỐI GIA HẠN ==================
def approve_borrow_extension_request(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền xác nhận gia hạn.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    record = BorrowRecord.query.get(record_id)

    if not record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    refresh_overdue_records(record.user_id)

    if record.status != "borrowing":
        flash("Chỉ có thể xác nhận gia hạn cho phiếu đang mượn.", "warning")
        return redirect(next_url)

    if getattr(record, "extension_status", None) != "pending":
        flash("Phiếu này không có yêu cầu gia hạn đang chờ xử lý.", "warning")
        return redirect(next_url)

    max_extend_times = 1
    extend_count = record.extend_count or 0

    if extend_count >= max_extend_times:
        record.extension_status = "rejected"
        db.session.commit()
        flash(f"Phiếu này đã đạt tối đa {max_extend_times} lần gia hạn.", "warning")
        return redirect(next_url)

    max_extend_days = get_rule_max_borrow_days()
    extend_days = safe_int(getattr(record, "extension_days", 0), 0)

    if extend_days <= 0:
        flash("Số ngày gia hạn không hợp lệ.", "error")
        return redirect(next_url)

    if extend_days > max_extend_days:
        flash(
            f"Số ngày gia hạn vượt quá {max_extend_days} ngày theo quy định.",
            "error",
        )
        return redirect(next_url)

    record.due_date = record.due_date + timedelta(days=extend_days)
    record.extend_count = extend_count + 1
    record.extension_status = "approved"

    if hasattr(record, "extension_processed_at"):
        record.extension_processed_at = datetime.utcnow()

    if hasattr(record, "extension_processed_by"):
        record.extension_processed_by = current_user.id if current_user else None

    db.session.commit()

    flash(f"Đã xác nhận gia hạn thêm {extend_days} ngày.", "success")
    return redirect(next_url)


def reject_borrow_extension_request(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền từ chối gia hạn.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    record = BorrowRecord.query.get(record_id)

    if not record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    if getattr(record, "extension_status", None) != "pending":
        flash("Phiếu này không có yêu cầu gia hạn đang chờ xử lý.", "warning")
        return redirect(next_url)

    record.extension_status = "rejected"
    record.extend_count = 1

    if hasattr(record, "extension_processed_at"):
        record.extension_processed_at = datetime.utcnow()

    if hasattr(record, "extension_processed_by"):
        record.extension_processed_by = current_user.id if current_user else None

    db.session.commit()

    flash("Đã từ chối yêu cầu gia hạn.", "success")
    return redirect(next_url)


# ================== ADMIN: XỬ LÝ PHIẾU TRỄ HẠN ==================
def process_overdue_allow(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền xử lý phiếu trễ hạn.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    record = BorrowRecord.query.get(record_id)

    if not record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    if record.status != "overdue":
        flash("Chỉ xử lý được phiếu đang trễ hạn.", "warning")
        return redirect(next_url)

    mark_record_items_returned(record)

    record.status = "overdue_processed"

    if getattr(record, "extension_status", None) == "pending":
        record.extension_status = "rejected"

    add_return_record(
        record,
        current_user,
        note="Đã xử lý trả trễ và cho phép mượn lại.",
    )

    db.session.commit()

    flash("Đã xử lý trả trễ. Độc giả được phép mượn lại.", "success")
    return redirect(next_url)


def process_overdue_ban(record_id):
    next_url = get_next_url("/admin?tab=borrow&view=records")

    if not is_admin_or_librarian():
        flash("Bạn không có quyền xử lý phiếu trễ hạn.", "error")
        return redirect(next_url)

    current_user = get_current_user()
    record = BorrowRecord.query.get(record_id)

    if not record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(next_url)

    if record.status != "overdue":
        flash("Chỉ xử lý được phiếu đang trễ hạn.", "warning")
        return redirect(next_url)

    mark_record_items_returned(record)

    record.status = "borrow_banned"

    if getattr(record, "extension_status", None) == "pending":
        record.extension_status = "rejected"

    user = User.query.get(record.user_id)
    if user:
        user.status = "locked"

    add_return_record(
        record,
        current_user,
        note="Đã xử lý trả trễ và cấm mượn.",
    )

    db.session.commit()

    flash("Đã xử lý trả trễ và cấm mượn độc giả này.", "success")
    return redirect(next_url)
