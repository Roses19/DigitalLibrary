from flask import render_template, session, redirect, url_for, flash
from sqlalchemy import text
from ThuVienSo import db
from ThuVienSo.data.models.user import User


def borrow_history_controller():
    username = session.get("username")

    if not username:
        flash("Vui lòng đăng nhập để xem lịch sử mượn sách.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=username).first()

    if not user:
        flash("Không tìm thấy người dùng.", "error")
        return redirect(url_for("auth.login"))

    sql = """
        SELECT 
            br.id AS borrow_record_id,
            br.borrow_date,
            br.due_date,
            br.status AS borrow_status,

            bri.quantity,
            bri.returned_quantity,
            bri.item_status,

            b.id AS book_id,
            b.title AS book_title,
            b.cover_image
        FROM borrow_records br
        JOIN borrow_record_items bri 
            ON br.id = bri.borrow_record_id
        JOIN books b 
            ON bri.book_id = b.id
        WHERE br.user_id = :user_id
        ORDER BY br.borrow_date DESC, br.id DESC
    """

    histories = db.session.execute(
        text(sql),
        {"user_id": user.id}
    ).mappings().all()

    return render_template(
        "borrow/history.html",
        histories=histories
    )