
from ThuVienSo.services.excel_service import export_excel
from ThuVienSo.services.pdf_service import export_pdf

from flask import render_template
from sqlalchemy import func
from datetime import datetime

from ThuVienSo import db
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.book_copy import BookCopy


def report_dashboard():
    total_borrow = BorrowRecord.query.count()

    borrowing = BorrowRecord.query.filter_by(
        status="borrowing"
    ).count()

    returned = BorrowRecord.query.filter_by(
        status="returned"
    ).count()

    overdue = BorrowRecord.query.filter(
        BorrowRecord.due_date < datetime.utcnow(),
        BorrowRecord.status == "borrowing"
    ).count()

    # SÁCH SẮP HẾT
    low_stock = (
        db.session.query(func.sum(BookCopy.available_quantity))
        .filter(BookCopy.available_quantity <= 2)
        .scalar()
    ) or 0

    return render_template(
        "admin/reports.html",
        total_borrow=total_borrow,
        borrowing=borrowing,
        returned=returned,
        overdue=overdue,
        low_stock=low_stock
    )

def export_excel_report():
    return export_excel()


def export_pdf_report():
    return export_pdf()