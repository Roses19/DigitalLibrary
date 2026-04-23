from flask import Blueprint
from ThuVienSo.controller.borrow_controller import borrow_history_controller

borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")


@borrow_bp.route("/history")
def history():
    return borrow_history_controller()