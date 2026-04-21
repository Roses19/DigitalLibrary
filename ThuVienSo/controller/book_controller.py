from flask import request, render_template

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
