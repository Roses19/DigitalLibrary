from flask import Blueprint

from ThuVienSo.controller.admin_controller import (
    admin_dashboard,
    list_users,
    create_user,
    update_user,
    toggle_user_status,
    delete_user,
)

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("", methods=["GET"])
@admin_bp.route("/", methods=["GET"])
def dashboard():
    return admin_dashboard()


@admin_bp.route("/users", methods=["GET"])
def users():
    return list_users()


@admin_bp.route("/users/create", methods=["POST"])
def user_create():
    return create_user()


@admin_bp.route("/users/<int:user_id>/edit", methods=["POST"])
def user_edit(user_id):
    return update_user(user_id)


@admin_bp.route("/users/<int:user_id>/status", methods=["POST"])
def user_status(user_id):
    return toggle_user_status(user_id)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
def user_delete(user_id):
    return delete_user(user_id)