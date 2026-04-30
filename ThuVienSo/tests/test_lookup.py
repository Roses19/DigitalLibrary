"""
Test case 4.1.5 - Tra cứu lịch sử mượn sách
Kiểm tra phân quyền và chức năng tra cứu của thủ thư/admin.
"""
from unittest.mock import patch, MagicMock


def _make_user(role_name, authenticated=True):
    """Tạo mock user với role cho trước."""
    mock_role = MagicMock()
    mock_role.name = role_name
    mock_user = MagicMock()
    mock_user.is_authenticated = authenticated
    mock_user.is_active = True
    mock_user.is_anonymous = False
    mock_user.get_id.return_value = '1'
    mock_user.role = mock_role
    return mock_user


def test_lookup_requires_login(client):
    """Chưa đăng nhập → trả về 401."""
    res = client.get('/borrow/lookup')
    assert res.status_code == 401


def test_lookup_accessible_by_librarian(client):
    """Thủ thư đăng nhập → truy cập được trang tra cứu."""
    mock_user = _make_user('thủ thư')

    with patch('flask_login.utils._get_user', return_value=mock_user), \
         patch('ThuVienSo.controller.borrow_controller.current_user', mock_user), \
         patch('ThuVienSo.controller.borrow_controller.db') as mock_db:

        mock_db.session.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get('/borrow/lookup')
        assert res.status_code == 200


def test_lookup_denied_for_reader(client):
    """Độc giả không có quyền → redirect hoặc 403."""
    mock_user = _make_user('độc giả')

    with patch('flask_login.utils._get_user', return_value=mock_user), \
         patch('ThuVienSo.controller.borrow_controller.current_user', mock_user):
        res = client.get('/borrow/lookup')
        assert res.status_code in (302, 403)


def test_lookup_with_keyword(client):
    """Tra cứu với từ khóa → không crash (mock DB)."""
    mock_user = _make_user('admin')

    with patch('flask_login.utils._get_user', return_value=mock_user), \
         patch('ThuVienSo.controller.borrow_controller.current_user', mock_user), \
         patch('ThuVienSo.controller.borrow_controller.db') as mock_db:

        mock_db.session.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get('/borrow/lookup?q=nguyen')
        assert res.status_code == 200


def test_lookup_with_status_filter(client):
    """Lọc theo trạng thái borrowing → không crash."""
    mock_user = _make_user('admin')

    with patch('flask_login.utils._get_user', return_value=mock_user), \
         patch('ThuVienSo.controller.borrow_controller.current_user', mock_user), \
         patch('ThuVienSo.controller.borrow_controller.db') as mock_db:

        mock_db.session.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get('/borrow/lookup?status=borrowing')
        assert res.status_code == 200


def test_lookup_with_date_range(client):
    """Lọc theo khoảng ngày → không crash."""
    mock_user = _make_user('admin')

    with patch('flask_login.utils._get_user', return_value=mock_user), \
         patch('ThuVienSo.controller.borrow_controller.current_user', mock_user), \
         patch('ThuVienSo.controller.borrow_controller.db') as mock_db:

        mock_db.session.execute.return_value.mappings.return_value.all.return_value = []

        res = client.get('/borrow/lookup?from_date=2026-04-01&to_date=2026-04-30')
        assert res.status_code == 200
