from flask import Blueprint, render_template

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin')
def admin_dashboard():
    return render_template('admin/dashboard.html')