from flask import Blueprint

from ThuVienSo import db
from ThuVienSo.controller.auth_controller import register_controller, login_controller, logout_controller

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from ThuVienSo.controller.auth_controller import (
    get_user_by_email,
    reset_user_password
)

from ThuVienSo.data.models.user import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    return register_controller()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return login_controller()

@auth.route('/logout')
def logout():
    return logout_controller()

@auth.route(
    "/forgot_password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        confirm_password = (
            request.form["confirm_password"]
        )

        user = (
            User.query
            .filter_by(email=email)
            .first()
        )

        if not user:

            flash(
                "Email không tồn tại.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        if password != confirm_password:

            flash(
                "Mật khẩu xác nhận không khớp.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        user.password_hash = password

        db.session.commit()

        flash(
            "Đổi mật khẩu thành công.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/rpass.html"
    )