from flask import Blueprint, render_template
from sqlalchemy.orm import joinedload
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.branch import Branch
from ThuVienSo.controller.admin_controller import (
    admin_dashboard,
    list_users,
    create_user,
    update_user,
    toggle_user_status,
    delete_user,
)

from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.role import Role
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from ThuVienSo import db
from ThuVienSo.data.models.rule import LibraryRule

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


@admin_bp.route("", methods=["GET"])
@admin_bp.route("/", methods=["GET"])
def dashboard():
    users = User.query.order_by(User.id.asc()).all()
    roles = Role.query.order_by(Role.id.asc()).all()

    # BOOKS (🔥 QUAN TRỌNG)
    books = Book.query.options(
        joinedload(Book.copies).joinedload(BookCopy.branch),
        joinedload(Book.category),
        joinedload(Book.publisher)
    ).order_by(Book.id.desc()).all()

    categories = Category.query.all()
    publishers = Publisher.query.all()
    branches = Branch.query.all()
    rule = LibraryRule.query.filter_by(is_active=True).first()

    active_section = request.args.get("section", "books")

    return render_template(
        "admin/dashboard.html",
        users=users,
        roles=roles,

        books=books,
        categories=categories,
        publishers=publishers,
        branches=branches,
        rule=rule,
        active_section=active_section
    )

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

#-----rule------
@admin_bp.route('/rules', methods=['GET', 'POST'])
def manage_rules():
    rule = LibraryRule.query.filter_by(is_active=True).first()
    if request.method == 'POST':
        rule.max_books_per_borrow = int(request.form.get('max_books_per_borrow'))
        rule.max_borrow_days = int(request.form.get('max_borrow_days'))
        rule.max_extend_times = int(request.form.get('max_extend_times'))

        db.session.commit()
        flash("Cập nhật quy định thành công!", "success")
        return redirect(url_for("admin_bp.dashboard", section="rules"))
    return redirect(url_for("admin_bp.dashboard"))