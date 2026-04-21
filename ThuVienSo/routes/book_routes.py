from flask import Blueprint
from ThuVienSo.controller.book_controller import search_books, get_book_detail

book_bp = Blueprint("book", __name__, url_prefix="/books")


@book_bp.route("/search")
def search():
    return search_books()


@book_bp.route("/<int:book_id>")
def detail(book_id):
    return get_book_detail(book_id)
