from flask import Blueprint
from flask_login import login_required

from ThuVienSo.controller.borrow_controller import (
    borrow_history_controller,
    borrow_manage_controller,
    borrow_lookup_controller,
    return_book_controller,
)

borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")


@borrow_bp.route("/history")
@login_required
def history():
    return borrow_history_controller()


@borrow_bp.route("/manage")
@login_required
def manage():
    return borrow_manage_controller()


@borrow_bp.route("/lookup")
@login_required
def lookup():
    return borrow_lookup_controller()


@borrow_bp.route("/return/<int:record_id>", methods=["POST"])
@login_required
def return_book(record_id):
    return return_book_controller(record_id)
