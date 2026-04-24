from flask import Flask
from ThuVienSo import init_app
from ThuVienSo.routes.home_routes import home_bp
from ThuVienSo.routes.book_routes import book_bp
from ThuVienSo.routes.admin_routes import admin_bp

app = Flask(__name__)
app.secret_key = "digital-library-secret-key"

init_app(app)
app.register_blueprint(home_bp)
app.register_blueprint(book_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
