from flask import Blueprint
from ThuVienSo.controller.book_controller import (
    search_books,
    advanced_search_controller,
    get_book_detail,
    get_categories,
    create_category,
    update_category,
    delete_category, get_book_list, get_admin_book_list, create_book, update_book, delete_book, update_book_copy,
    create_book_copy
)


book_bp = Blueprint("book", __name__, url_prefix="/books")


@book_bp.route("/search")
def search():
    return search_books()


@book_bp.route("/advanced-search", methods=["GET"])
def advanced_search():
    return advanced_search_controller()

@book_bp.route("/<int:book_id>")
def detail(book_id):
    return get_book_detail(book_id)


@book_bp.route("/categories")
def categories():
    return get_categories()


@book_bp.route("/categories/create", methods=["POST"])
def category_create():
    return create_category()


@book_bp.route("/categories/<int:category_id>/edit", methods=["POST"])
def category_edit(category_id):
    return update_category(category_id)


@book_bp.route("/categories/<int:category_id>/delete", methods=["POST"])
def category_delete(category_id):
    return delete_category(category_id)



@book_bp.route("/list")
def book_list():
    return get_book_list()


@book_bp.route("/admin")
def admin_book_list():
    return get_admin_book_list()


@book_bp.route("/admin/create", methods=["POST"])
def book_create():
    return create_book()


@book_bp.route("/admin/<int:book_id>/edit", methods=["POST"])
def book_edit(book_id):
    return update_book(book_id)

@book_bp.route("/copy/<int:copy_id>/edit", methods=["POST"])
def book_copy_edit(copy_id):
    return update_book_copy(copy_id)

@book_bp.route("/copy/<int:book_id>/create", methods=["POST"])
def book_copy_create(book_id):
    return create_book_copy(book_id)

@book_bp.route("/admin/<int:book_id>/delete", methods=["POST"])
def book_delete(book_id):
    return delete_book(book_id)