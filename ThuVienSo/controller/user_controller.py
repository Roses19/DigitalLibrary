from flask import render_template, session, redirect, url_for, flash, request
from ThuVienSo import db
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.role import Role

def profile():
    username = session.get("username")

    if not username:
        flash("Vui lòng đăng nhập để xem thông tin cá nhân.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("Không tìm thấy thông tin người dùng.", "error")
        return redirect(url_for("auth.login"))

    return render_template("user/profile.html", user=user)


def update_profile_controller():
    username = session.get("username")

    if not username:
        flash("Vui lòng đăng nhập để cập nhật thông tin.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("auth.login"))

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()

    if not full_name or not email:
        flash("Họ tên và email không được để trống.", "error")
        return redirect(url_for("user.user_profile"))

    existed_email = User.query.filter(
        User.email == email,
        User.id != user.id
    ).first()

    if existed_email:
        flash("Email này đã được sử dụng.", "error")
        return redirect(url_for("user.user_profile"))

    user.full_name = full_name
    user.email = email
    user.phone = phone if phone else None

    db.session.commit()

    flash("Cập nhật thông tin thành công.", "success")
    return redirect(url_for("user.user_profile"))


def reader_list_controller():
    username = session.get("username")

    if not username:
        flash("Vui lòng đăng nhập.", "error")
        return redirect(url_for("auth.login"))

    current_user = User.query.filter_by(username=username).first()

    if not current_user:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("auth.login"))

    # Tạm thời bỏ check admin để test giao diện
    readers = User.query.order_by(User.id.asc()).all()

    return render_template("admin/readers.html", readers=readers)