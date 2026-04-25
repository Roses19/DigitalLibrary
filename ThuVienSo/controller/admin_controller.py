from flask import render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from ThuVienSo import db
from ThuVienSo.controller.borrow_controller import safe_int
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.role import Role
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher

USER_STATUSES = ["active", "locked", "inactive"]
BOOK_STATUSES = ["available", "out_of_stock"]

def _get_next_url(default="/admin?tab=users"):
    return request.form.get("next_url") or default


def _role_name(user):
    return (user.role.name if user and user.role else "").strip().lower()


def _is_admin(user):
    return _role_name(user) in {"admin", "quản trị", "quản trị viên"}


def _is_last_admin(user):
    if not _is_admin(user):
        return False

    admin_roles = Role.query.filter(
        Role.name.in_(["admin", "Quản trị", "Quản trị viên"])
    ).all()

    admin_role_ids = [role.id for role in admin_roles]

    if not admin_role_ids:
        return False

    return (
        User.query
        .filter(
            User.role_id.in_(admin_role_ids),
            User.status != "locked"
        )
        .count()
        <= 1
    )


def get_request_status_label(status):
    labels = {
        "pending": "Chờ duyệt",
        "approved": "Đã duyệt",
        "rejected": "Đã từ chối"
    }

    return labels.get(status, status)


def get_record_status_label(status):
    labels = {
        "borrowing": "Đang mượn",
        "returned": "Đã trả"
    }

    return labels.get(status, status)

def admin_dashboard():
    active_tab = request.args.get("tab", "users").strip()
    selected_status = request.args.get("status", "").strip()
    selected_view = request.args.get("view", "").strip()
    selected_category = request.args.get("category", "").strip()

    # USERS
    users = User.query.order_by(User.id.asc()).all()
    roles = Role.query.order_by(Role.id.asc()).all()

    book_query = Book.query

    # BOOKS
    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    books = (
        Book.query
        .options(joinedload(Book.copies))
        .order_by(Book.created_at.desc())
        .all()
    )

    if selected_category:
        category_id = safe_int(selected_category)

        if category_id:
            book_query = book_query.filter(Book.category_id == category_id)

    books = book_query.order_by(Book.id.asc()).all()

    # BORROWS
    borrow_requests = []
    borrow_records = []

    if active_tab == "borrow":
        if selected_view == "records":
            borrow_records = (
                BorrowRecord.query
                .order_by(BorrowRecord.borrow_date.desc())
                .all()
            )
        else:
            query = BorrowRequest.query

            if selected_status:
                query = query.filter(BorrowRequest.status == selected_status)

            borrow_requests = (
                query
                .order_by(BorrowRequest.created_at.desc())
                .all()
            )

    return render_template(
        "admin/dashboard.html",

        active_tab=active_tab,
        selected_status=selected_status,
        selected_view=selected_view,
        selected_category=selected_category,

        users=users,
        roles=roles,
        statuses=USER_STATUSES,

        books=books,
        categories=categories,
        publishers=publishers,

        borrow_requests=borrow_requests,
        borrow_records=borrow_records,
        get_request_status_label=get_request_status_label,
        get_record_status_label=get_record_status_label,
    )

def list_users():
    users = User.query.order_by(User.id.asc()).all()
    roles = Role.query.order_by(Role.id.asc()).all()
    return render_template(
        "admin/users.html",
        users=users,
        roles=roles,
        statuses=USER_STATUSES,
    )


def create_user():
    next_url = _get_next_url()

    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id", "").strip()
    status = request.form.get("status", "active").strip()

    if not full_name or not username or not email or not password:
        flash("Họ tên, username, email và mật khẩu không được để trống.", "error")
        return redirect(next_url)

    role = Role.query.get(role_id) if role_id else None

    if role is None:
        flash("Vai trò không hợp lệ.", "error")
        return redirect(next_url)

    if status not in USER_STATUSES:
        flash("Trạng thái không hợp lệ.", "error")
        return redirect(next_url)

    if User.query.filter(db.func.lower(User.username) == username.lower()).first():
        flash(f'Username "{username}" đã tồn tại.', "error")
        return redirect(next_url)

    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        flash(f'Email "{email}" đã tồn tại.', "error")
        return redirect(next_url)

    user = User(
        full_name=full_name,
        username=username,
        email=email,
        phone=phone,
        role_id=role.id,
        status=status,
        password_hash=generate_password_hash(password),
    )

    db.session.add(user)
    db.session.commit()

    flash(f'Đã thêm người dùng "{username}".', "success")
    return redirect(next_url)


def update_user(user_id):
    next_url = _get_next_url()

    user = User.query.get(user_id)

    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(next_url)

    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id", "").strip()
    status = request.form.get("status", "active").strip()

    if not full_name or not username or not email:
        flash("Họ tên, username và email không được để trống.", "error")
        return redirect(next_url)

    role = Role.query.get(role_id) if role_id else None

    if role is None:
        flash("Vai trò không hợp lệ.", "error")
        return redirect(next_url)

    if status not in USER_STATUSES:
        flash("Trạng thái không hợp lệ.", "error")
        return redirect(next_url)

    username_exists = (
        User.query
        .filter(
            db.func.lower(User.username) == username.lower(),
            User.id != user_id,
        )
        .first()
    )

    if username_exists:
        flash(f'Username "{username}" đã tồn tại.', "error")
        return redirect(next_url)

    email_exists = (
        User.query
        .filter(
            db.func.lower(User.email) == email.lower(),
            User.id != user_id,
        )
        .first()
    )

    if email_exists:
        flash(f'Email "{email}" đã tồn tại.', "error")
        return redirect(next_url)

    old_is_last_admin = _is_last_admin(user)
    new_role_is_admin = role.name.strip().lower() in {
        "admin",
        "quản trị",
        "quản trị viên"
    }

    if old_is_last_admin and (not new_role_is_admin or status == "locked"):
        flash("Không thể đổi vai trò hoặc khóa admin cuối cùng.", "error")
        return redirect(next_url)

    user.full_name = full_name
    user.username = username
    user.email = email
    user.phone = phone
    user.role_id = role.id
    user.status = status

    if password:
        user.password_hash = generate_password_hash(password)

    db.session.commit()

    flash(f'Đã cập nhật người dùng "{username}".', "success")
    return redirect(next_url)


def toggle_user_status(user_id):
    next_url = _get_next_url()

    user = User.query.get(user_id)

    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(next_url)

    if _is_last_admin(user) and user.status == "active":
        flash("Không thể khóa admin cuối cùng.", "error")
        return redirect(next_url)

    if user.status == "active":
        user.status = "locked"
        flash(f'Đã khóa người dùng "{user.username}".', "success")
    else:
        user.status = "active"
        flash(f'Đã mở khóa người dùng "{user.username}".', "success")

    db.session.commit()

    return redirect(next_url)


def delete_user(user_id):
    next_url = _get_next_url()

    user = User.query.get(user_id)

    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(next_url)

    if _is_last_admin(user):
        flash("Không thể xóa admin cuối cùng.", "error")
        return redirect(next_url)

    username = user.username

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa người dùng "{username}".', "success")
    except IntegrityError:
        db.session.rollback()
        flash(
            "Không thể xóa người dùng vì có dữ liệu liên quan. Hãy khóa tài khoản thay thế.",
            "error"
        )

    return redirect(next_url)
