from flask import Blueprint
from ThuVienSo.controller.auth_controller import register_controller, login_controller, logout_controller

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    return register_controller()

@auth.route('/login', methods=['GET', 'POST'])
def login():
    return login_controller()

@auth.route('/logout')
def logout():
    return logout_controller()