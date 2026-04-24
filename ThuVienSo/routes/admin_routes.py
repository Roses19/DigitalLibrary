from flask import Blueprint, render_template

from ThuVienSo.controller.admin_controller import (
    list_users,
    create_user,
    update_user,
    toggle_user_status,
    delete_user,
)

from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.role import Role

admin_bp = Blueprint("admin_bp", __name__)


# ================== DASHBOARD ==================
@admin_bp.route("/admin")
def admin_dashboard():
    users = User.query.order_by(User.id.asc()).all()
    roles = Role.query.order_by(Role.id.asc()).all()

    return render_template(
        "admin/dashboard.html",
        users=users,
        roles=roles
    )


# ================== USERS ==================
@admin_bp.route("/admin/users")
def users():
    return list_users()


@admin_bp.route("/admin/users/create", methods=["POST"])
def user_create():
    return create_user()


@admin_bp.route("/admin/users/<int:user_id>/edit", methods=["POST"])
def user_edit(user_id):
    return update_user(user_id)


@admin_bp.route("/admin/users/<int:user_id>/status", methods=["POST"])
def user_status(user_id):
    return toggle_user_status(user_id)


@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
def user_delete(user_id):
    return delete_user(user_id)