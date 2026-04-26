from flask import Blueprint, render_template
from ThuVienSo.controller.book_controller import get_home_books
from ThuVienSo.controller.borrow_controller import get_user_borrow_states

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    books = get_home_books()
    user_borrow_states = get_user_borrow_states()

    return render_template(
        "home/index.html",
        books=books,
        user_borrow_states=user_borrow_states
    )

@home_bp.route("/about")
def about():
    return render_template("home/about.html")