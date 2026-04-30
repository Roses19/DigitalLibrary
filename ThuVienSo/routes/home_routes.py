from flask import Blueprint, render_template
from ThuVienSo.controller.borrow_controller import get_user_borrow_states

from ThuVienSo.controller.book_controller import (
    get_home_books,
    get_user_borrow_states,
    get_dropdown_data,
)

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    featured_books = get_home_books()
    categories, publishers, branches = get_dropdown_data()

    return render_template(
        "home/index.html",
        featured_books=featured_books,
        books=featured_books,
        categories=categories,
        publishers=publishers,
        branches=branches,
        user_borrow_states=get_user_borrow_states(),
        show_advanced=True
    )

@home_bp.route("/about")
def about():
    return render_template("home/about.html")