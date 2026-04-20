from flask import request, redirect, url_for, flash, render_template, session
from werkzeug.security import generate_password_hash
from ThuVienSo import db
from ThuVienSo.data.models.user import User
from ThuVienSo.data.models.role import Role
from flask_login import login_user

from ThuVienSo.data.models.role import Role


def register_controller():


    return render_template('auth/register.html')
def login_controller():

    return render_template('auth/login.html')

def logout_controller():
    session.clear()
    return redirect(url_for('index'))