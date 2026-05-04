from flask_mail import Mail, Message
from datetime import datetime, timedelta

from ThuVienSo.data.models.borrow_record import BorrowRecord

mail = Mail()


# =========================
# GỬI EMAIL CHUNG
# =========================
def send_email(subject, recipients, body):

    print("SENDING MAIL TO:", recipients)

    msg = Message(
        subject=subject,
        recipients=recipients,
        body=body,
        sender="phuongnhu308@gmail.com"
    )

    mail.send(msg)

    print("MAIL SENT")


# =========================
# EMAIL NHẮC TRẢ SÁCH
# =========================
def send_due_reminder_emails():

    print("RUNNING REMINDER EMAIL")

    tomorrow = datetime.now() + timedelta(days=1)

    records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == "borrowing"
        )
        .all()
    )

    print("TOTAL RECORDS:", len(records))

    for r in records:

        print("RECORD:", r.id)
        print("DUE:", r.due_date.date())
        print("STATUS:", r.status)

        if r.due_date.date() == tomorrow.date():

            print("REMINDER FOUND")

            body = f"""
Xin chào {r.user.full_name},

Sách bạn đang mượn sẽ đến hạn vào ngày:
{r.due_date.strftime("%d/%m/%Y")}

Vui lòng trả sách đúng hạn.

Thư viện số
"""

            try:

                print("USER:", r.user)
                print("EMAIL:", r.user.email)

                send_email(
                    subject="Nhắc trả sách",
                    recipients=[r.user.email],
                    body=body
                )

                print("Đã gửi reminder:", r.user.email)

            except Exception as e:
                print("MAIL ERROR:", e)


# =========================
# EMAIL CẢNH BÁO QUÁ HẠN
# =========================
def send_overdue_warning_emails():

    print("RUNNING OVERDUE EMAIL")

    today = datetime.now().date()

    records = (
        BorrowRecord.query
        .filter(
            BorrowRecord.status == "borrowing"
        )
        .all()
    )

    print("TODAY:", today)
    print("TOTAL RECORDS:", len(records))

    for r in records:

        print("RECORD:", r.id)
        print("DUE:", r.due_date.date())
        print("STATUS:", r.status)

        if r.due_date.date() < today:

            print("OVERDUE FOUND")

            late_days = (
                today - r.due_date.date()
            ).days

            body = f"""
Xin chào {r.user.full_name},

Bạn đã trễ hạn trả sách {late_days} ngày.

Vui lòng trả sách sớm nhất có thể.

Thư viện số
"""

            try:

                print("USER:", r.user)
                print("EMAIL:", r.user.email)

                print("BEFORE SEND")

                send_email(
                    subject="Cảnh báo trễ hạn",
                    recipients=[r.user.email],
                    body=body
                )

                print("Đã gửi overdue:", r.user.email)

            except Exception as e:
                print("MAIL ERROR:", e)


# =========================
# CHẠY TOÀN BỘ EMAIL TỰ ĐỘNG
# =========================
def run_auto_email_jobs():

    print("AUTO JOB START")

    send_due_reminder_emails()

    send_overdue_warning_emails()