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
    delete_borrow_request,
    request_borrow_extension,
    approve_borrow_extension_request,
    reject_borrow_extension_request,
    process_overdue_allow,
    process_overdue_ban,
    borrow_manage_controller,
    borrow_lookup_controller,
    return_book_controller,
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


# ================== USER: LỊCH SỬ MƯỢN ==================
@borrow_bp.route("/history", methods=["GET"])
def history():
    return get_borrow_history()


# ================== USER: SỬA / XÓA YÊU CẦU MƯỢN ==================
@borrow_bp.route("/request/<int:borrow_id>/edit", methods=["GET"])
def edit_form(borrow_id):
    return show_edit_borrow_request_form(borrow_id)


@borrow_bp.route("/request/<int:borrow_id>/edit", methods=["POST"])
def update_request(borrow_id):
    return update_borrow_request(borrow_id)


@borrow_bp.route("/request/<int:borrow_id>/delete", methods=["POST"])
def delete_request(borrow_id):
    return delete_borrow_request(borrow_id)


# ================== USER: GỬI YÊU CẦU GIA HẠN ==================
# GET: mở trang nhập số ngày gia hạn
# POST: gửi yêu cầu gia hạn
@borrow_bp.route("/record/<int:record_id>/extend", methods=["GET", "POST"])
def extend_record(record_id):
    return request_borrow_extension(record_id)


# ================== ADMIN: DANH SÁCH YÊU CẦU MƯỢN ==================
@borrow_bp.route("/admin", methods=["GET"])
def admin_list():
    return get_admin_borrow_requests()


# ================== ADMIN: DUYỆT / TỪ CHỐI YÊU CẦU MƯỢN ==================
@borrow_bp.route("/admin/<int:borrow_id>/approve", methods=["POST"])
def approve(borrow_id):
    return approve_borrow_request(borrow_id)


@borrow_bp.route("/admin/<int:borrow_id>/reject", methods=["POST"])
def reject(borrow_id):
    return reject_borrow_request(borrow_id)


# ================== ADMIN: PHIẾU MƯỢN ĐÃ DUYỆT ==================
@borrow_bp.route("/admin/records", methods=["GET"])
def admin_records():
    return get_admin_borrow_records()


# ================== ADMIN: XÁC NHẬN TRẢ SÁCH ==================
@borrow_bp.route("/admin/records/<int:record_id>/return", methods=["POST"])
def return_record(record_id):
    return return_borrow_record(record_id)


# ================== ADMIN: XÁC NHẬN / TỪ CHỐI GIA HẠN ==================
@borrow_bp.route("/admin/record/<int:record_id>/extension/approve", methods=["POST"])
def approve_extension(record_id):
    return approve_borrow_extension_request(record_id)


@borrow_bp.route("/admin/record/<int:record_id>/extension/reject", methods=["POST"])
def reject_extension(record_id):
    return reject_borrow_extension_request(record_id)


# ================== ADMIN: XỬ LÝ PHIẾU TRỄ HẠN ==================
@borrow_bp.route("/admin/record/<int:record_id>/overdue/allow", methods=["POST"])
def overdue_allow(record_id):
    return process_overdue_allow(record_id)


@borrow_bp.route("/admin/record/<int:record_id>/overdue/ban", methods=["POST"])
def overdue_ban(record_id):
    return process_overdue_ban(record_id)


# ================== THỦ THƯ: QUẢN LÝ / TRA CỨU / TRẢ SÁCH ==================
@borrow_bp.route("/manage", methods=["GET"])
def manage():
    return borrow_manage_controller()


@borrow_bp.route("/lookup", methods=["GET"])
def lookup():
    return borrow_lookup_controller()


# Route cũ nếu template/code cũ đang gọi borrow.return_book
@borrow_bp.route("/return/<int:record_id>", methods=["POST"])
def return_book(record_id):
    return return_book_controller(record_id)