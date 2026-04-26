from datetime import datetime

from flask import render_template, session, redirect, url_for, flash, request
from flask_login import current_user, login_required
from sqlalchemy import text

from ThuVienSo import db
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem
from ThuVienSo.data.models.return_record import ReturnRecord
from ThuVienSo.data.models.user import User


# ================== ĐỘC GIẢ: lịch sử mượn ==================
def borrow_history_controller():
    username = session.get("username")

    if not username:
        flash("Vui lòng đăng nhập để xem lịch sử mượn sách.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("auth.login"))

    sql = """
        SELECT
            br.id AS borrow_record_id,
            br.borrow_date,
            br.due_date,
            br.status AS borrow_status,
            bri.quantity,
            bri.returned_quantity,
            bri.item_status,
            b.id AS book_id,
            b.title AS book_title,
            b.cover_image
        FROM borrow_records br
        JOIN borrow_record_items bri ON br.id = bri.borrow_record_id
        JOIN books b ON bri.book_id = b.id
        WHERE br.user_id = :user_id
        ORDER BY br.borrow_date DESC, br.id DESC
    """

    histories = db.session.execute(text(sql), {"user_id": user.id}).mappings().all()
    return render_template("borrow/history.html", histories=histories)


# ================== THỦ THƯ/ADMIN: tra cứu lịch sử mượn ==================
def borrow_lookup_controller():
    role_name = (current_user.role.name if current_user.role else "").strip().lower()
    if role_name not in {"thủ thư", "librarian", "admin", "quản trị", "quản trị viên"}:
        flash("Bạn không có quyền truy cập trang này.", "error")
        return redirect(url_for("home.index"))

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
        conditions.append("br.status = :status")
        params["status"] = status_filter

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


# ================== THỦ THƯ: danh sách đang mượn ==================
def borrow_manage_controller():
    role_name = (current_user.role.name if current_user.role else "").strip().lower()
    if role_name not in {"thủ thư", "librarian", "admin", "quản trị", "quản trị viên"}:
        flash("Bạn không có quyền truy cập trang này.", "error")
        return redirect(url_for("home.index"))

    active_records = (
        BorrowRecord.query
        .filter(BorrowRecord.status == "borrowing")
        .order_by(BorrowRecord.borrow_date.asc())
        .all()
    )

    returned_records = (
        BorrowRecord.query
        .filter(BorrowRecord.status == "returned")
        .order_by(BorrowRecord.borrow_date.desc())
        .limit(50)
        .all()
    )

    return render_template(
        "borrow/manage.html",
        active_records=active_records,
        returned_records=returned_records,
        now=datetime.now(),
    )


# ================== THỦ THƯ: xác nhận trả sách ==================
def return_book_controller(record_id):
    role_name = (current_user.role.name if current_user.role else "").strip().lower()
    if role_name not in {"thủ thư", "librarian", "admin", "quản trị", "quản trị viên"}:
        flash("Bạn không có quyền thực hiện thao tác này.", "error")
        return redirect(url_for("home.index"))

    record = BorrowRecord.query.get(record_id)
    if not record:
        flash("Không tìm thấy phiếu mượn.", "error")
        return redirect(url_for("borrow.manage"))

    if record.status == "returned":
        flash("Phiếu mượn này đã được trả trước đó.", "warning")
        return redirect(url_for("borrow.manage"))

    note = request.form.get("note", "").strip()
    now = datetime.now()

    for item in record.items:
        remaining = item.quantity - item.returned_quantity
        if remaining > 0:
            item.returned_quantity = item.quantity
            item.item_status = "returned"
            item.book.available_quantity += remaining

    record.status = "returned"

    return_rec = ReturnRecord(
        borrow_record_id=record.id,
        processed_by=current_user.id,
        return_date=now,
        note=note if note else None,
        created_at=now,
    )
    db.session.add(return_rec)
    db.session.commit()

    flash(f"Đã xác nhận trả sách cho phiếu #{record.id}.", "success")
    return redirect(url_for("borrow.manage"))
