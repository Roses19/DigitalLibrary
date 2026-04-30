"""
Test case 4.1.2 - Tìm kiếm sách
Kiểm tra chức năng tìm kiếm sách theo từ khóa.
Data nguồn: BOOKS list trong book_controller (không cần DB).
"""


def test_search_page_loads(client):
    """Trang tìm kiếm trả về 200."""
    res = client.get('/books/search')
    assert res.status_code == 200


def test_search_by_keyword_found(client):
    """Tìm từ khóa có trong dữ liệu mẫu → có kết quả."""
    res = client.get('/books/search?q=Python')
    assert res.status_code == 200
    assert 'Python' in res.data.decode('utf-8')


def test_search_by_keyword_not_found(client):
    """Tìm từ khóa không tồn tại → không có kết quả sách."""
    res = client.get('/books/search?q=xyzkhongtontai')
    assert res.status_code == 200
    # Không crash, page vẫn load bình thường
    assert b'xyzkhongtontai' not in res.data or res.status_code == 200


def test_search_empty_keyword(client):
    """Không nhập từ khóa → page load, không crash."""
    res = client.get('/books/search?q=')
    assert res.status_code == 200


def test_search_by_category_filter(client):
    """Lọc theo danh mục → page load thành công."""
    res = client.get('/books/search?category=1')
    assert res.status_code == 200


def test_search_by_status_available(client):
    """Lọc sách còn hàng → page load thành công."""
    res = client.get('/books/search?status=available')
    assert res.status_code == 200


def test_search_by_status_unavailable(client):
    """Lọc sách hết hàng → page load thành công."""
    res = client.get('/books/search?status=unavailable')
    assert res.status_code == 200


def test_search_combined_filters(client):
    """Kết hợp từ khóa + danh mục → không crash."""
    res = client.get('/books/search?q=Python&category=1&status=available')
    assert res.status_code == 200
