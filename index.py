import os

from dotenv import load_dotenv
from flask import Flask, session

from ThuVienSo import init_app
from ThuVienSo.routes.home_routes import home_bp
from ThuVienSo.routes.book_routes import book_bp
from ThuVienSo.routes.auth_routes import auth
from ThuVienSo.routes.borrow_routes import borrow_bp
from ThuVienSo.routes.admin_routes import admin_bp
from ThuVienSo.routes.user_routes import user_bp
from ThuVienSo.controller.borrow_controller import get_user_borrow_state_for_book
from ThuVienSo.services.mail_service import mail, run_auto_email_jobs

load_dotenv()

app = Flask(
    __name__,
    template_folder="ThuVienSo/templates",
    static_folder="ThuVienSo/static",
    static_url_path="/static"
)

app.secret_key = os.getenv("SECRET_KEY", "digital-library-dev-secret")

init_app(app)

app.register_blueprint(home_bp)
app.register_blueprint(book_bp)
app.register_blueprint(auth)
app.register_blueprint(borrow_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)


@app.context_processor
def inject_borrow_helpers():
    overdue_alert = session.pop("overdue_login_alert", False)
    overdue_count = session.pop("overdue_login_count", 0) if overdue_alert else 0

    return {
        "get_user_borrow_state_for_book": get_user_borrow_state_for_book,
        "login_overdue_alert": overdue_alert,
        "login_overdue_count": overdue_count,
    }


app.jinja_env.globals["get_user_borrow_state_for_book"] = get_user_borrow_state_for_book

app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv(
    "MAIL_DEFAULT_SENDER",
    app.config["MAIL_USERNAME"]
)

mail.init_app(app)


def scheduled_job():
    with app.app_context():
        run_auto_email_jobs()


# Không tự chạy scheduler trên PythonAnywhere web process.
# Chỉ bật khi bạn set ENABLE_SCHEDULER=true trong .env local.
if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
    from apscheduler.schedulers.background import BackgroundScheduler

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=scheduled_job,
        trigger="interval",
        hours=24
    )
    scheduler.start()


if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False,
        port=5000
    )