from flask import Blueprint, request, flash, redirect, url_for

from ThuVienSo import db
from ThuVienSo.controller.admin_controller import (
    admin_dashboard,
    list_users,
    create_user,
    update_user,
    toggle_user_status,
    delete_user,
)
from ThuVienSo.data.models.rule import LibraryRule
from ThuVienSo.services.excel_service import export_report_excel


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


@admin_bp.route("/rules", methods=["GET", "POST"])
def manage_rules():
    rule = LibraryRule.query.filter_by(is_active=True).first()

    if request.method == "POST":
        if not rule:
            rule = LibraryRule(is_active=True)
            db.session.add(rule)

        rule.max_books_per_borrow = int(request.form.get("max_books_per_borrow", 3))
        rule.max_borrow_days = int(request.form.get("max_borrow_days", 14))
        rule.max_extend_times = int(request.form.get("max_extend_times", 1))

        db.session.commit()
        flash("Cập nhật quy định thành công!", "success")

    return redirect(url_for("admin_bp.dashboard", tab="rules"))


admin_bp.add_url_rule(
    "/report/export/excel",
    view_func=export_report_excel,
    endpoint="export_report_excel"
)