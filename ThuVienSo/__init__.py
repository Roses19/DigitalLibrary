from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import LoginManager
from urllib.parse import quote

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()


def init_app(app):
    # ===== CONFIG MYSQL =====
    app.config["SQLALCHEMY_DATABASE_URI"] = \
        "mysql+pymysql://root:%s@localhost/digital_library?charset=utf8mb4" % quote('12345678')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key'

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
