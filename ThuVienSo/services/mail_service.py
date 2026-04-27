from flask_mail import Mail, Message
from datetime import datetime, timedelta

from ThuVienSo.data.models.borrow_record import BorrowRecord

mail = Mail()


# =========================
# GỬI EMAIL CHUNG
# =========================
def send_email(subject, recipients, body):

    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender="Thư viện số"
    )

    mail.send(msg)


# =========================
# EMAIL NHẮC TRẢ SÁCH
# =========================
def send_due_reminder_emails():

    tomorrow = datetime.utcnow() + timedelta(days=1)

    records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == "borrowing"
        )
        .all()
    )

    for r in records:

        if r.due_date.date() == tomorrow.date():

            body = f"""
Xin chào {r.user.full_name},

Sách bạn đang mượn sẽ đến hạn vào ngày:
{r.due_date.strftime("%d/%m/%Y")}

Vui lòng trả sách đúng hạn.

Thư viện số
"""

            send_email(
                subject="Nhắc trả sách",
                recipients=[r.user.email],
                body=body
            )


# =========================
# EMAIL CẢNH BÁO QUÁ HẠN
# =========================
def send_overdue_warning_emails():

    today = datetime.utcnow().date()

    records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == "borrowing"
        )
        .all()
    )

    for r in records:

        if r.due_date.date() < today:

            late_days = (
                today - r.due_date.date()
            ).days

            body = f"""
Xin chào {r.user.full_name},

Bạn đã trễ hạn trả sách {late_days} ngày.

Vui lòng trả sách sớm nhất có thể.

Thư viện số
"""

            send_email(
                subject="Cảnh báo trễ hạn",
                recipients=[r.user.email],
                body=body
            )


# =========================
# CHẠY TOÀN BỘ EMAIL TỰ ĐỘNG
# =========================
def run_auto_email_jobs():

    send_due_reminder_emails()

    send_overdue_warning_emails()