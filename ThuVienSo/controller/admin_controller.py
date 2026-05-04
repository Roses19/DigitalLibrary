from datetime import datetime

from flask import render_template, request, redirect, flash, session
from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash

from ThuVienSo import db
from ThuVienSo.controller.borrow_controller import (
    get_borrow_item_branch_name,
    get_record_item_branch_name,
    refresh_overdue_records,
    safe_int,
)
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.branch import Branch
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.role import Role
from ThuVienSo.data.models.rule import LibraryRule
from ThuVienSo.data.models.user import User


USER_STATUSES = ["active", "locked", "inactive"]
BOOK_STATUSES = ["available", "out_of_stock"]


def _get_next_url(default="/admin?tab=users"):
    return request.form.get("next_url") or request.args.get("next_url") or default


def _get_current_user():
    user_id = session.get("user_id")

    if user_id:
        return User.query.get(user_id)

    username = session.get("username")

    if username:
        return User.query.filter_by(username=username).first()

    return None


def _role_name(user):
    return (user.role.name if user and user.role else "").strip().lower()


def _is_admin(user):
    return _role_name(user) in {
        "admin",
        "quản trị",
        "quan tri",
        "quản trị viên",
        "quan tri vien",
    }


def _is_librarian(user):
    return _role_name(user) in {
        "thủ thư",
        "thu thu",
        "librarian",
    }


def _get_visible_users_for_current_user():
    current_user = _get_current_user()

    query = User.query.options(joinedload(User.role))

    if current_user:
        query = query.filter(User.id != current_user.id)

    if _is_librarian(current_user):
        query = query.join(Role).filter(
            func.lower(Role.name).in_(["độc giả", "doc gia", "reader"])
        )

    return query.order_by(User.id.asc()).all()


def _can_access_admin_module(user, module_name):
    if not user or user.status != "active":
        return False

    if _is_admin(user):
        return True

    if _is_librarian(user):
        return module_name in {
            "books",
            "borrow",
            "borrow_lookup",
            "borrow_manage",
        }

    return False


def _is_last_admin(user):
    if not _is_admin(user):
        return False

    admin_roles = Role.query.filter(
        Role.name.in_([
            "admin",
            "Admin",
            "Quản trị",
            "quản trị",
            "Quản trị viên",
            "quản trị viên",
        ])
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
        "rejected": "Đã từ chối",
    }

    return labels.get(status, status)


def get_record_status_label(status):
    if status == "overdue":
        return "Trễ hạn"

    labels = {
        "borrowing": "Đang mượn",
        "returned": "Đã trả",
    }

    return labels.get(status, status)


def get_lookup_records(keyword="", status_filter="", from_date="", to_date=""):
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

    return db.session.execute(text(sql), params).mappings().all()


def admin_dashboard():
    refresh_overdue_records()

    current_user = _get_current_user()

    active_tab = request.args.get("tab", "users").strip()
    selected_status = request.args.get("status", "").strip()
    selected_view = request.args.get("view", "").strip()
    selected_category = request.args.get("category", "").strip()

    users = _get_visible_users_for_current_user()
    roles = Role.query.order_by(Role.id.asc()).all()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()
    branches = Branch.query.order_by(Branch.name.asc()).all()

    book_query = Book.query

    if selected_category:
        category_id = safe_int(selected_category, 0)

        if category_id:
            book_query = book_query.filter(Book.category_id == category_id)

    if _is_librarian(current_user):
        if getattr(current_user, "branch_id", None):
            book_query = (
                book_query
                .join(BookCopy)
                .filter(BookCopy.branch_id == current_user.branch_id)
                .distinct()
            )
        else:
            book_query = book_query.filter(False)

    books = (
        book_query
        .options(joinedload(Book.copies).joinedload(BookCopy.branch))
        .order_by(Book.id.asc())
        .all()
    )

    rule = LibraryRule.query.filter_by(is_active=True).first()

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

    keyword = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "").strip()
    from_date = request.args.get("from_date", "").strip()
    to_date = request.args.get("to_date", "").strip()

    lookup_records = []

    if active_tab == "borrow_lookup":
        lookup_records = get_lookup_records(
            keyword=keyword,
            status_filter=status_filter,
            from_date=from_date,
            to_date=to_date,
        )

    total_borrow = BorrowRecord.query.count()
    borrowing = BorrowRecord.query.filter_by(status="borrowing").count()
    returned = BorrowRecord.query.filter_by(status="returned").count()

    overdue = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status.in_(["borrowing", "overdue"]),
            BorrowRecord.due_date < datetime.utcnow()
        )
        .count()
    )

    returned_on_time = BorrowRecord.query.filter_by(status="returned").count()
    not_returned = borrowing
    total_titles = Book.query.count()

    total_book_quantity = (
        db.session.query(func.sum(BookCopy.total_quantity)).scalar()
    ) or 0

    available_books = (
        db.session.query(func.sum(BookCopy.available_quantity)).scalar()
    ) or 0

    borrowed_books = total_book_quantity - available_books
    borrow_percent = 0

    if total_book_quantity > 0:
        borrow_percent = round((borrowed_books / total_book_quantity) * 100, 1)

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
        branches=branches,
        borrow_requests=borrow_requests,
        borrow_records=borrow_records,
        rule=rule,
        get_request_status_label=get_request_status_label,
        get_record_status_label=get_record_status_label,
        get_borrow_item_branch_name=get_borrow_item_branch_name,
        get_record_item_branch_name=get_record_item_branch_name,
        total_borrow=total_borrow,
        borrowing=borrowing,
        returned=returned,
        overdue=overdue,
        returned_on_time=returned_on_time,
        not_returned=not_returned,
        total_titles=total_titles,
        total_book_quantity=total_book_quantity,
        available_books=available_books,
        borrowed_books=borrowed_books,
        borrow_percent=borrow_percent,
        lookup_records=lookup_records,
        keyword=keyword,
        status_filter=status_filter,
        from_date=from_date,
        to_date=to_date,
        now=datetime.now(),
    )


def list_users():
    users = _get_visible_users_for_current_user()
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
    branch_id = request.form.get("branch_id") or None

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

    if hasattr(user, "branch_id"):
        user.branch_id = safe_int(branch_id, None) if branch_id else None

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
    branch_id = request.form.get("branch_id") or None

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
        "quan tri",
        "quản trị viên",
        "quan tri vien",
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

    if hasattr(user, "branch_id"):
        user.branch_id = safe_int(branch_id, None) if branch_id else None

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