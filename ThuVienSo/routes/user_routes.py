from flask import Blueprint
from ThuVienSo.controller.user_controller import profile, update_profile_controller
from ThuVienSo.controller.user_controller import reader_list_controller

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/profile")
def user_profile():
    return profile()


@user_bp.route("/update", methods=["POST"])
def update_profile():
    return update_profile_controller()

@user_bp.route("/readers")
def readers():
    return reader_list_controller()
