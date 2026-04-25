from flask import render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ThuVienSo import db
from ThuVienSo.data.models.role import Role
from ThuVienSo.data.models.user import User

USER_STATUSES = ["active", "locked", "inactive"]


def _role_name(user):
    return (user.role.name if user and user.role else "").strip().lower()


def _is_admin(user):
    return _role_name(user) in {"admin", "quản trị", "quản trị viên"}


def _is_last_admin(user):
    if not _is_admin(user):
        return False
    admin_roles = Role.query.filter(Role.name.in_(["admin", "Quản trị", "Quản trị viên"])).all()
    admin_role_ids = [role.id for role in admin_roles]
    if not admin_role_ids:
        return False
    return User.query.filter(User.role_id.in_(admin_role_ids), User.status != "locked").count() <= 1


def admin_dashboard():
    return render_template("admin/dashboard.html")


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
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id", "").strip()
    status = request.form.get("status", "active").strip()

    if not full_name or not username or not email or not password:
        flash("Họ tên, username, email và mật khẩu không được để trống.", "error")
        return redirect(url_for("admin_bp.users"))

    role = Role.query.get(role_id) if role_id else None
    if role is None:
        flash("Vai trò không hợp lệ.", "error")
        return redirect(url_for("admin_bp.users"))

    if status not in USER_STATUSES:
        flash("Trạng thái không hợp lệ.", "error")
        return redirect(url_for("admin_bp.users"))

    if User.query.filter(db.func.lower(User.username) == username.lower()).first():
        flash(f'Username "{username}" đã tồn tại.', "error")
        return redirect(url_for("admin_bp.users"))

    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        flash(f'Email "{email}" đã tồn tại.', "error")
        return redirect(url_for("admin_bp.users"))

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
    return redirect(url_for("admin_bp.users"))


def update_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("admin_bp.users"))

    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "").strip()
    role_id = request.form.get("role_id", "").strip()
    status = request.form.get("status", "active").strip()

    if not full_name or not username or not email:
        flash("Họ tên, username và email không được để trống.", "error")
        return redirect(url_for("admin_bp.users"))

    role = Role.query.get(role_id) if role_id else None
    if role is None:
        flash("Vai trò không hợp lệ.", "error")
        return redirect(url_for("admin_bp.users"))

    if status not in USER_STATUSES:
        flash("Trạng thái không hợp lệ.", "error")
        return redirect(url_for("admin_bp.users"))

    username_exists = User.query.filter(
        db.func.lower(User.username) == username.lower(),
        User.id != user_id,
    ).first()
    if username_exists:
        flash(f'Username "{username}" đã tồn tại.', "error")
        return redirect(url_for("admin_bp.users"))

    email_exists = User.query.filter(
        db.func.lower(User.email) == email.lower(),
        User.id != user_id,
    ).first()
    if email_exists:
        flash(f'Email "{email}" đã tồn tại.', "error")
        return redirect(url_for("admin_bp.users"))

    old_is_last_admin = _is_last_admin(user)
    new_role_is_admin = role.name.strip().lower() in {"admin", "quản trị", "quản trị viên"}
    if old_is_last_admin and (not new_role_is_admin or status == "locked"):
        flash("Không thể đổi vai trò hoặc khóa admin cuối cùng.", "error")
        return redirect(url_for("admin_bp.users"))

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
    return redirect(url_for("admin_bp.users"))


def toggle_user_status(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("admin_bp.users"))

    if _is_last_admin(user) and user.status == "active":
        flash("Không thể khóa admin cuối cùng.", "error")
        return redirect(url_for("admin_bp.users"))

    user.status = "locked" if user.status == "active" else "active"
    db.session.commit()
    flash(f'Đã cập nhật trạng thái người dùng "{user.username}".', "success")
    return redirect(url_for("admin_bp.users"))


def delete_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("admin_bp.users"))

    if _is_last_admin(user):
        flash("Không thể xóa admin cuối cùng.", "error")
        return redirect(url_for("admin_bp.users"))

    username = user.username
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'Đã xóa người dùng "{username}".', "success")
    except IntegrityError:
        db.session.rollback()
        flash("Không thể xóa người dùng vì có dữ liệu liên quan. Hãy khóa tài khoản thay thế.", "error")
    return redirect(url_for("admin_bp.users"))
