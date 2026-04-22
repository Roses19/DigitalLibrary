from flask import Blueprint
from ThuVienSo.controller.book_controller import (
    search_books,
    advanced_search_controller,
    get_book_detail,
    get_categories,
    create_category,
    update_category,
    delete_category,
)
book_bp = Blueprint("book", __name__, url_prefix="/books")


@book_bp.route("/search", methods=["GET"])
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

