from flask import Blueprint, render_template
from sqlalchemy.orm import joinedload
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.branch import Branch
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


    # BOOKS (🔥 QUAN TRỌNG)
    books = Book.query.options(
        joinedload(Book.copies).joinedload(BookCopy.branch),
        joinedload(Book.category),
        joinedload(Book.publisher)
    ).order_by(Book.id.desc()).all()

    categories = Category.query.all()
    publishers = Publisher.query.all()
    branches = Branch.query.all()

    return render_template(
        "admin/dashboard.html",
        users=users,
        roles=roles,

        # 👇 thêm mấy cái này
        books=books,
        categories=categories,
        publishers=publishers,
        branches=branches,

        active_section="books"  # mặc định mở tab books
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

