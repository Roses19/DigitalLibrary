from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from sqlalchemy import text

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()


def init_app(app):
    # ===== CONFIG MYSQL =====
    from config import (
        SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS,
        SQLALCHEMY_ENGINE_OPTIONS,
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = SQLALCHEMY_ENGINE_OPTIONS

    # ===== INIT EXTENSIONS =====
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    # ===== USER LOADER =====
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ===== LOAD MODELS =====
    with app.app_context():
        from ThuVienSo.data.models.user import User
        from ThuVienSo.data.models.role import Role
        from ThuVienSo.data.models.borrow_request import BorrowRequest
        from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
        from ThuVienSo.data.models.borrow_record import BorrowRecord
        from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem
        from ThuVienSo.data.models.return_record import ReturnRecord

        for column_name, column_sql in {
            "extend_count": "INT DEFAULT 0",
            "extension_status": "VARCHAR(20) NULL",
            "extension_requested_at": "DATETIME NULL",
        }.items():
            exists = db.session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'borrow_records'
                      AND COLUMN_NAME = :column_name
                    """
                ),
                {"column_name": column_name},
            ).scalar()

            if not exists:
                db.session.execute(
                    text(f"ALTER TABLE borrow_records ADD COLUMN {column_name} {column_sql}")
                )

        db.session.commit()