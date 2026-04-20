from flask import Blueprint, render_template
from ThuVienSo.controller.book_controller import get_home_books

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    books = get_home_books()
    return render_template("home/index.html", books=books)
