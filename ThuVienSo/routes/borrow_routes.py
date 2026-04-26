from flask import Blueprint

from ThuVienSo.controller.borrow_controller import (
    show_borrow_form,
    create_borrow_request,
    get_borrow_history,
    get_admin_borrow_requests,
    get_admin_borrow_records,
    approve_borrow_request,
    reject_borrow_request,
    return_borrow_record,
    show_edit_borrow_request_form,
    update_borrow_request,
    delete_borrow_request
)


borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")

# Alias nếu index.py cũ từng import borrow_manage_bp
borrow_manage_bp = borrow_bp


# ================== USER: MƯỢN SÁCH ==================
@borrow_bp.route("/request/<int:book_id>", methods=["GET"])
def borrow_form(book_id):
    return show_borrow_form(book_id)


@borrow_bp.route("/request/<int:book_id>", methods=["POST"])
def request_borrow(book_id):
    return create_borrow_request(book_id)


@borrow_bp.route("/history")
def history():
    return get_borrow_history()


@borrow_bp.route("/request/<int:borrow_id>/edit", methods=["GET"])
def edit_form(borrow_id):
    return show_edit_borrow_request_form(borrow_id)


@borrow_bp.route("/request/<int:borrow_id>/edit", methods=["POST"])
def update_request(borrow_id):
    return update_borrow_request(borrow_id)


@borrow_bp.route("/request/<int:borrow_id>/delete", methods=["POST"])
def delete_request(borrow_id):
    return delete_borrow_request(borrow_id)


# ================== ADMIN: DUYỆT MƯỢN ==================
@borrow_bp.route("/admin")
def admin_list():
    return get_admin_borrow_requests()


@borrow_bp.route("/admin/<int:borrow_id>/approve", methods=["POST"])
def approve(borrow_id):
    return approve_borrow_request(borrow_id)


@borrow_bp.route("/admin/<int:borrow_id>/reject", methods=["POST"])
def reject(borrow_id):
    return reject_borrow_request(borrow_id)


# ================== ADMIN: PHIẾU MƯỢN ĐÃ DUYỆT ==================
@borrow_bp.route("/admin/records")
def admin_records():
    return get_admin_borrow_records()


@borrow_bp.route("/admin/records/<int:record_id>/return", methods=["POST"])
def return_record(record_id):
    return return_borrow_record(record_id)