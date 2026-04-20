from flask import Flask
from ThuVienSo.routes.home_routes import home_bp
from ThuVienSo.routes.book_routes import book_bp

app = Flask(__name__)

app.register_blueprint(home_bp)
app.register_blueprint(book_bp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
