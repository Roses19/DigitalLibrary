from flask import Blueprint
from ThuVienSo.controller.report_controller import (
    report_dashboard,
    export_excel_report,
    export_pdf_report,
)

report_bp = Blueprint(
    "report",
    __name__,
    url_prefix="/reports"
)


@report_bp.route("/")
def dashboard():
    return report_dashboard()


@report_bp.route("/excel")
def export_excel():
    return export_excel_report()


@report_bp.route("/pdf")
def export_pdf():
    return export_pdf_report()