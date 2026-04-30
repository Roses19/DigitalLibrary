import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, Flask
from ThuVienSo.routes.book_routes import book_bp
from ThuVienSo.routes.borrow_routes import borrow_bp
from ThuVienSo.routes.home_routes import home_bp
from ThuVienSo.routes.admin_routes import admin_bp


def _make_auth_bp():
    auth_bp = Blueprint('auth', __name__)

    @auth_bp.route('/login')
    def login():
        return 'login', 200

    return auth_bp


@pytest.fixture
def app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    )
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from ThuVienSo import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = None

    app.register_blueprint(home_bp)
    app.register_blueprint(book_bp)
    app.register_blueprint(borrow_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(_make_auth_bp())

    with app.app_context():
        from ThuVienSo.data.models.role import Role
        from ThuVienSo.data.models.user import User

        # Stub tables cho các model chưa được implement (của thành viên khác)
        # Cần thiết để SQLAlchemy resolve FK khi create_all
        from sqlalchemy import Table, Column, Integer, String, Text
        if 'categories' not in db.metadata.tables:
            Table('categories', db.metadata,
                  Column('id', Integer, primary_key=True),
                  Column('name', String(100)))
        if 'books' not in db.metadata.tables:
            Table('books', db.metadata,
                  Column('id', Integer, primary_key=True),
                  Column('title', String(255)),
                  Column('available_quantity', Integer, default=0),
                  Column('category_id', Integer))

        from ThuVienSo.data.models.borrow_request import BorrowRequest
        from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
        from ThuVienSo.data.models.borrow_record import BorrowRecord
        from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem
        from ThuVienSo.data.models.return_record import ReturnRecord

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        db.create_all()

    return app


@pytest.fixture
def client(app):
    return app.test_client()
