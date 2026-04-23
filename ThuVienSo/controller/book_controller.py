from flask import request, render_template, redirect, url_for, flash

CATEGORIES = [
    {"id": 1, "name": "Công nghệ",   "description": "Sách về lập trình, CNTT, kỹ thuật phần mềm.", "book_count": 3},
    {"id": 2, "name": "Toán học",    "description": "Giáo trình toán đại học và phổ thông.",        "book_count": 1},
    {"id": 3, "name": "Khoa học",    "description": "Vật lý, Hóa học, Sinh học đại cương.",         "book_count": 1},
    {"id": 4, "name": "Văn học",     "description": "Tác phẩm văn học trong và ngoài nước.",        "book_count": 0},
    {"id": 5, "name": "Kinh tế",     "description": "Kinh tế học, quản trị kinh doanh.",            "book_count": 0},
]

_category_id_counter = 6
_book_id_counter = 6

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


def get_book_list():
    category_filter = request.args.get("category", "").strip()
    if category_filter:
        filtered = [b for b in BOOKS if b["category"] == category_filter]
    else:
        filtered = list(BOOKS)
    return render_template(
        "books/list.html",
        books=filtered,
        categories=CATEGORIES,
        selected_category=category_filter,
    )


def get_admin_book_list():
    category_filter = request.args.get("category", "").strip()
    if category_filter:
        filtered = [b for b in BOOKS if b["category"] == category_filter]
    else:
        filtered = list(BOOKS)
    return render_template(
        "books/list_admin.html",
        books=filtered,
        categories=CATEGORIES,
        selected_category=category_filter,
    )


def create_book():
    global _book_id_counter
    title        = request.form.get("title", "").strip()
    author       = request.form.get("author", "").strip()
    category     = request.form.get("category", "").strip()
    description  = request.form.get("description", "").strip()
    cover        = request.form.get("cover", "").strip()
    quantity_str = request.form.get("quantity", "1").strip()

    if not title or not author or not category:
        flash("Tên sách, tác giả và danh mục không được để trống.", "error")
        return redirect(url_for("book.admin_book_list"))

    try:
        quantity = int(quantity_str)
        if quantity < 0:
            raise ValueError
    except ValueError:
        flash("Số lượng phải là số nguyên không âm.", "error")
        return redirect(url_for("book.admin_book_list"))

    if not cover:
        cover = f"https://placehold.co/200x280?text={title[:10].replace(' ', '+')}"

    BOOKS.append({
        "id": _book_id_counter,
        "title": title,
        "author": author,
        "category": category,
        "description": description,
        "cover": cover,
        "quantity": quantity,
    })

    cat = next((c for c in CATEGORIES if c["name"] == category), None)
    if cat:
        cat["book_count"] += 1

    _book_id_counter += 1
    flash(f'Đã thêm sách "{title}".', "success")
    return redirect(url_for("book.admin_book_list"))


def update_book(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if book is None:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("book.admin_book_list"))

    title        = request.form.get("title", "").strip()
    author       = request.form.get("author", "").strip()
    category     = request.form.get("category", "").strip()
    description  = request.form.get("description", "").strip()
    cover        = request.form.get("cover", "").strip()
    quantity_str = request.form.get("quantity", "0").strip()

    if not title or not author or not category:
        flash("Tên sách, tác giả và danh mục không được để trống.", "error")
        return redirect(url_for("book.admin_book_list"))

    try:
        quantity = int(quantity_str)
        if quantity < 0:
            raise ValueError
    except ValueError:
        flash("Số lượng phải là số nguyên không âm.", "error")
        return redirect(url_for("book.admin_book_list"))

    old_category = book["category"]
    if old_category != category:
        old_cat = next((c for c in CATEGORIES if c["name"] == old_category), None)
        new_cat = next((c for c in CATEGORIES if c["name"] == category), None)
        if old_cat and old_cat["book_count"] > 0:
            old_cat["book_count"] -= 1
        if new_cat:
            new_cat["book_count"] += 1

    book.update({
        "title": title,
        "author": author,
        "category": category,
        "description": description,
        "cover": cover or book["cover"],
        "quantity": quantity,
    })

    flash(f'Đã cập nhật sách "{title}".', "success")
    return redirect(url_for("book.admin_book_list"))


def delete_book(book_id):
    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if book is None:
        flash("Không tìm thấy sách.", "error")
        return redirect(url_for("book.admin_book_list"))

    cat = next((c for c in CATEGORIES if c["name"] == book["category"]), None)
    if cat and cat["book_count"] > 0:
        cat["book_count"] -= 1

    BOOKS.remove(book)
    flash(f'Đã xóa sách "{book["title"]}".', "success")
    return redirect(url_for("book.admin_book_list"))


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
