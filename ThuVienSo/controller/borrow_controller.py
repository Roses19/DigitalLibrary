from datetime import datetime, timedelta

from flask import render_template, redirect, url_for, flash, session, request

from ThuVienSo import db
from ThuVienSo.data.models.book import Book
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


def get_user_borrow_states():
    current_user = get_current_user()

    if not current_user:
        return {}

    borrow_items = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(
            BorrowRequest.user_id == current_user.id,
            BorrowRequest.status.in_(["pending", "approved"])
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
            BorrowRequest.status.in_(["pending", "approved"])
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

    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect("/books/list")

    available_quantity = book.available_quantity or 0

    if available_quantity <= 0:
        flash("Sách này hiện đã hết, không thể mượn.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    # Chỉ phiếu đang chờ duyệt mới chuyển sang sửa phiếu.
    # Phiếu đã duyệt thì vẫn được mượn lại.
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
        return redirect(url_for("borrow.edit_form", borrow_id=pending_item.borrow_request_id))

    return render_template(
        "borrow/request.html",
        book=book,
        available_quantity=available_quantity,
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

    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách.", "error")
        return redirect("/books/list")

    available_quantity = book.available_quantity or 0

    if available_quantity <= 0:
        flash("Sách này hiện đã hết, không thể mượn.", "error")
        return redirect(url_for("book.detail", book_id=book.id))

    try:
        quantity = int(request.form.get("quantity", 1))
    except ValueError:
        quantity = 1

    note = request.form.get("note", "").strip()

    if quantity <= 0:
        flash("Số lượng mượn phải lớn hơn 0.", "error")
        return redirect(url_for("borrow.borrow_form", book_id=book.id))

    if quantity > available_quantity:
        flash(f"Số lượng mượn không được vượt quá số sách còn lại ({available_quantity}).", "error")
        return redirect(url_for("borrow.borrow_form", book_id=book.id))

    # Chỉ chặn nếu đang có phiếu pending.
    # Phiếu approved thì cho phép mượn lại.
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
    book = item.book
    available_quantity = book.available_quantity or 0

    return render_template(
        "borrow/request.html",
        book=book,
        available_quantity=available_quantity,
        edit_mode=True,
        borrow_request=borrow_request,
        item=item,
        form_action=url_for("borrow.update_request", borrow_id=borrow_request.id),
        quantity=item.quantity,
        note=borrow_request.note or "",
        page_title="Sửa yêu cầu mượn sách",
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
    book = item.book
    available_quantity = book.available_quantity or 0

    quantity = safe_int(request.form.get("quantity"), 1)
    note = request.form.get("note", "").strip()

    if quantity <= 0:
        flash("Số lượng mượn phải lớn hơn 0.", "error")
        return redirect(url_for("borrow.edit_form", borrow_id=borrow_request.id))

    if quantity > available_quantity:
        flash(f"Số lượng mượn không được vượt quá số sách còn lại ({available_quantity}).", "error")
        return redirect(url_for("borrow.edit_form", borrow_id=borrow_request.id))

    item.quantity = quantity
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

    for item in borrow_request.items:
        book = item.book

        if not book:
            flash("Có sách trong yêu cầu không tồn tại.", "error")
            return redirect(next_url)

        available_quantity = book.available_quantity or 0

        if available_quantity < item.quantity:
            flash(f'Sách "{book.title}" không đủ số lượng để duyệt.', "error")
            return redirect(next_url)

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
        book = item.book

        record_item = BorrowRecordItem(
            borrow_record_id=borrow_record.id,
            book_id=item.book_id,
            quantity=item.quantity,
            returned_quantity=0,
            item_status="borrowing",
        )

        db.session.add(record_item)

        book.available_quantity = (book.available_quantity or 0) - item.quantity

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
        book = item.book
        not_returned_quantity = item.quantity - (item.returned_quantity or 0)

        if not book:
            continue

        if not_returned_quantity > 0:
            book.available_quantity = (book.available_quantity or 0) + not_returned_quantity
            item.returned_quantity = item.quantity
            item.item_status = "returned"

            if hasattr(book, "total_quantity") and book.total_quantity:
                if book.available_quantity > book.total_quantity:
                    book.available_quantity = book.total_quantity

    borrow_record.status = "returned"

    db.session.commit()

    flash("Đã xác nhận trả sách.", "success")
    return redirect(next_url)