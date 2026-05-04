from flask import request, redirect, url_for, flash, render_template, session
from werkzeug.security import generate_password_hash
from ThuVienSo import db
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.role import Role
from flask_login import login_user
from ThuVienSo.controller.borrow_controller import get_overdue_records

from ThuVienSo.data.models.role import Role


def register_controller():
    if request.method == 'POST':
        username = request.form['username']
        full_name=request.form['full_name']
        password = request.form['password']
        role_name = "Độc giả"
        email = request.form['email']
        phone = request.form['phonenumber']

        # check tồn tại
        if User.query.filter_by(username=username).first():
            flash('Tên đăng nhập đã tồn tại.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email đã tồn tại.', 'error')
            return redirect(url_for('auth.register'))

        # lấy role từ DB
        role = Role.query.filter_by(name=role_name).first()

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            full_name=full_name,
            password_hash=password,
            email=email,
            phone=phone,
            role_id=role.id,
            status="active"
        )

        db.session.add(new_user)
        db.session.commit()

        flash('Đăng ký thành công!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')
def login_controller():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            login_user(user)

            session['role'] = user.role.name
            overdue_records = get_overdue_records(user.id)
            if overdue_records:
                session['overdue_login_alert'] = True
                session['overdue_login_count'] = len(overdue_records)
            if user.role.name == 'Quản trị':
                return redirect(url_for('admin_bp.dashboard'))
            elif user.role.name == 'Thủ thư':
                return redirect(url_for('admin_bp.dashboard'))
            else:
                return redirect(url_for('home.index'))

        flash('Sai thông tin đăng nhập!', 'danger')

    return render_template('auth/login.html')

def logout_controller():
    session.clear()
    return redirect(url_for('home.index'))


def get_user_by_email(email):

    return (
        User.query
        .filter_by(email=email)
        .first()
    )


def reset_user_password(email, new_password):

    user = get_user_by_email(email)

    if not user:
        return False

    user.password_hash = new_password

    db.session.commit()

    return True