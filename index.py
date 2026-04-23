from flask import Flask
from ThuVienSo import init_app
from ThuVienSo.routes.home_routes import home_bp
from ThuVienSo.routes.book_routes import book_bp
from ThuVienSo.routes.auth_routes import auth
from ThuVienSo.routes.borrow_routes import borrow_manage_bp
from ThuVienSo.routes.admin_routes import admin_bp

app = Flask(
    __name__,
    template_folder="ThuVienSo/templates",
    static_folder="ThuVienSo/static",
    static_url_path="/static"
)
app.secret_key = "digital-library-secret-key"
init_app(app)
app.register_blueprint(home_bp)
app.register_blueprint(book_bp)
app.register_blueprint(auth)
app.register_blueprint(borrow_manage_bp)
app.register_blueprint(admin_bp)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
