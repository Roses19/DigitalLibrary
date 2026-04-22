from flask import request, render_template, redirect, url_for, flash

CATEGORIES = [
    {"id": 1, "name": "Công nghệ",   "description": "Sách về lập trình, CNTT, kỹ thuật phần mềm.", "book_count": 3},
    {"id": 2, "name": "Toán học",    "description": "Giáo trình toán đại học và phổ thông.",        "book_count": 1},
    {"id": 3, "name": "Khoa học",    "description": "Vật lý, Hóa học, Sinh học đại cương.",         "book_count": 1},
    {"id": 4, "name": "Văn học",     "description": "Tác phẩm văn học trong và ngoài nước.",        "book_count": 0},
    {"id": 5, "name": "Kinh tế",     "description": "Kinh tế học, quản trị kinh doanh.",            "book_count": 0},
]

_category_id_counter = 6

BOOKS = [
    {
        "id": 1,
        "title": "Lập trình Python cơ bản",
        "author": "Nguyễn Văn A",
        "category": "Công nghệ",
        "description": "Sách hướng dẫn lập trình Python từ cơ bản đến nâng cao.",
        "cover": "https://placehold.co/200x280?text=Python",
        "quantity": 5,
    },
    {
        "id": 2,
        "title": "Giải tích 1",
        "author": "Trần Thị B",
        "category": "Toán học",
        "description": "Giáo trình giải tích dành cho sinh viên đại học.",
        "cover": "https://placehold.co/200x280?text=Giai+Tich",
        "quantity": 3,
    },
    {
        "id": 3,
        "title": "Nhập môn Cơ sở dữ liệu",
        "author": "Lê Văn C",
        "category": "Công nghệ",
        "description": "Tổng quan về hệ quản trị cơ sở dữ liệu quan hệ.",
        "cover": "https://placehold.co/200x280?text=CSDL",
        "quantity": 0,
    },
    {
        "id": 4,
        "title": "Vật lý đại cương",
        "author": "Phạm Thị D",
        "category": "Khoa học",
        "description": "Giáo trình vật lý đại cương cho sinh viên năm nhất.",
        "cover": "https://placehold.co/200x280?text=Vat+Ly",
        "quantity": 2,
    },
    {
        "id": 5,
        "title": "Kỹ thuật lập trình",
        "author": "Hoàng Văn E",
        "category": "Công nghệ",
        "description": "Các kỹ thuật lập trình hiệu quả và tối ưu.",
        "cover": "https://placehold.co/200x280?text=KTLT",
        "quantity": 1,
    },
]


def get_categories():
    return render_template("books/categories.html", categories=CATEGORIES)


def create_category():
    global _category_id_counter
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    if any(c["name"].lower() == name.lower() for c in CATEGORIES):
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    CATEGORIES.append({
        "id": _category_id_counter,
        "name": name,
        "description": description,
        "book_count": 0,
    })
    _category_id_counter += 1
    flash(f'Đã thêm danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def update_category(category_id):
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    cat = next((c for c in CATEGORIES if c["id"] == category_id), None)

    if cat is None:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    if any(c["name"].lower() == name.lower() and c["id"] != category_id for c in CATEGORIES):
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    cat["name"] = name
    cat["description"] = description
    flash(f'Đã cập nhật danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def delete_category(category_id):
    cat = next((c for c in CATEGORIES if c["id"] == category_id), None)

    if cat is None:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    if cat["book_count"] > 0:
        flash(f'Không thể xóa danh mục "{cat["name"]}" vì đang có {cat["book_count"]} sách.', "error")
        return redirect(url_for("book.categories"))

    CATEGORIES.remove(cat)
    flash(f'Đã xóa danh mục "{cat["name"]}".', "success")
    return redirect(url_for("book.categories"))


def get_home_books():
    return BOOKS[:4]


def search_books():
    keyword = request.args.get("q", "").strip()
    if not keyword:
        return render_template("books/search.html", books=[], keyword="", searched=False)

    keyword_lower = keyword.lower()
    results = [
        b for b in BOOKS
        if keyword_lower in b["title"].lower()
        or keyword_lower in b["author"].lower()
        or keyword_lower in b["category"].lower()
    ]

    return render_template("books/search.html", books=results, keyword=keyword, searched=True)


def get_book_detail(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if book is None:
        return render_template("books/detail.html", book=None)
    return render_template("books/detail.html", book=book)
