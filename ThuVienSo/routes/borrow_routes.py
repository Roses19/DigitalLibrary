from flask import Blueprint, render_template

borrow_manage_bp = Blueprint('borrow_manage_bp', __name__)

@borrow_manage_bp.route('/borrow/management')
def borrow_management():
    return render_template('borrow/manage.html')