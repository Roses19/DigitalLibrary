from flask import request, render_template, redirect, url_for, flash, jsonify
from sqlalchemy.orm import joinedload

from ThuVienSo import db
from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.category import Category
from ThuVienSo.data.models.publisher import Publisher
from ThuVienSo.data.models.author import Author


# ================== HOME ==================
def get_home_books():
    return Book.query.order_by(Book.created_at.desc()).limit(4).all()



# ================== CATEGORY ==================
def get_categories():
    categories = Category.query.all()
    return render_template("books/categories.html", categories=categories)


def create_category():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    exists = Category.query.filter(db.func.lower(Category.name) == name.lower()).first()
    if exists:
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    new_category = Category(name=name, description=description)
    db.session.add(new_category)
    db.session.commit()

    flash(f'Đã thêm danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def update_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()

    if not name:
        flash("Tên danh mục không được để trống.", "error")
        return redirect(url_for("book.categories"))

    exists = Category.query.filter(
        db.func.lower(Category.name) == name.lower(),
        Category.id != category_id
    ).first()

    if exists:
        flash(f'Danh mục "{name}" đã tồn tại.', "error")
        return redirect(url_for("book.categories"))

    category.name = name
    category.description = description
    db.session.commit()

    flash(f'Đã cập nhật danh mục "{name}".', "success")
    return redirect(url_for("book.categories"))


def delete_category(category_id):
    category = Category.query.get(category_id)

    if not category:
        flash("Không tìm thấy danh mục.", "error")
        return redirect(url_for("book.categories"))

    if category.books:
        flash(f'Không thể xóa "{category.name}" vì đang có sách.', "error")
        return redirect(url_for("book.categories"))

    db.session.delete(category)
    db.session.commit()

    flash(f'Đã xóa "{category.name}".', "success")
    return redirect(url_for("book.categories"))


# ================== SEARCH ==================
def build_book_query(keyword="", category_ids=None, publisher_ids=None, status=""):
    query = Book.query

    category_ids = category_ids or []
    publisher_ids = publisher_ids or []

    if keyword:
        query = query.outerjoin(Book.authors).filter(
            db.or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.isbn.ilike(f"%{keyword}%"),
                Author.name.ilike(f"%{keyword}%")
            )
        )

    if category_ids:
        query = query.filter(Book.category_id.in_(category_ids))

    if publisher_ids:
        query = query.filter(Book.publisher_id.in_(publisher_ids))

    if status == "available":
        query = query.filter(Book.available_quantity > 0)

    elif status == "unavailable":
        query = query.filter(Book.available_quantity <= 0)

    return query.distinct()


def search_books():
    keyword = request.args.get("q", "").strip()

    selected_categories = request.args.getlist("category")
    selected_publishers = request.args.getlist("publisher")
    selected_status = request.args.get("status", "").strip()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    searched = bool(
        keyword or selected_categories or selected_publishers or selected_status
    )

    if searched:
        books = build_book_query(
            keyword=keyword,
            category_ids=selected_categories,
            publisher_ids=selected_publishers,
            status=selected_status
        ).order_by(Book.created_at.desc()).all()
    else:
        books = []

    return render_template(
        "books/search.html",
        books=books,
        keyword=keyword,
        searched=searched,
        categories=categories,
        publishers=publishers,
        selected_categories=selected_categories,
        selected_publishers=selected_publishers,
        selected_status=selected_status
    )


# ================== ADVANCED SEARCH ==================
def advanced_search_controller():
    keyword = request.args.get("q", "").strip()
    publisher_id = request.args.get("publisher_id", "").strip()
    category_id = request.args.get("category_id", "").strip()

    categories = Category.query.order_by(Category.name.asc()).all()
    publishers = Publisher.query.order_by(Publisher.name.asc()).all()

    query = Book.query

    if keyword:
        query = query.outerjoin(Book.authors).filter(
            db.or_(
                Book.title.ilike(f"%{keyword}%"),
                Book.isbn.ilike(f"%{keyword}%"),
                Author.name.ilike(f"%{keyword}%")
            )
        )

    if publisher_id:
        query = query.filter(Book.publisher_id == int(publisher_id))

    if category_id:
        query = query.filter(Book.category_id == int(category_id))

    books = query.distinct().order_by(Book.created_at.desc()).all()

    return render_template(
        "books/search.html",
        books=books,
        categories=categories,
        publishers=publishers,
        keyword=keyword,
        publisher_id=publisher_id,
        category_id=category_id
    )


# ================== DETAIL ==================
def get_book_detail(book_id):
    book = Book.query.options(joinedload(Book.copies)).get(book_id)
    if not book:
        return render_template("books/detail.html", book=None)

    total = sum(c.total_quantity or 0 for c in book.copies)
    available = sum(c.available_quantity or 0 for c in book.copies)

    return render_template(
        "books/detail.html",
        book=book,
        total=total,
        available=available
    )

# ================== BOOK LIST ==================
def get_book_list():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template("books/list.html", books=books)


# ================== ADMIN BOOK LIST ==================
from ThuVienSo.data.models.branch import Branch
def get_admin_book_list():
    books = (
        Book.query
        .options(joinedload(Book.copies))
        .order_by(Book.created_at.desc())
        .all()
    )

    categories = Category.query.all()
    publishers = Publisher.query.all()
    branches = Branch.query.all()

    for book in books:
        total = 0
        available = 0

        if book.copies:
            for copy in book.copies:
                total += copy.total_quantity or 0
                available += copy.available_quantity or 0

        # 👉 QUAN TRỌNG: đảm bảo luôn có attribute
        # book.total = total
        # book.available = available

    return render_template(
        "books/list_admin.html",
        books=books,
        categories=categories,
        publishers=publishers,
        branches=branches
    )

# ================== CREATE BOOK ==================
def create_book():
    title = request.form.get("title")
    isbn = request.form.get("isbn")
    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")
    branch_id = request.form.get("branch_id")
    shelf_location = request.form.get("shelf_location")
    total_quantity = int(request.form.get("total_quantity", 0))

    if not title:
        flash("Tên sách không được để trống", "error")
        return redirect(url_for("admin_bp.admin_dashboard"))

    # 👉 tạo book
    book = Book(
        title=title,
        isbn=isbn,
        category_id=int(category_id) if category_id else None,
        publisher_id=int(publisher_id) if publisher_id else None,
    )

    db.session.add(book)
    db.session.flush()  # 👉 để lấy book.id

    # 👉 tạo bản sao theo chi nhánh
    if branch_id:
        copy = BookCopy(
            book_id=book.id,
            branch_id=int(branch_id),
            shelf_location=shelf_location,
            total_quantity=total_quantity,
            available_quantity=total_quantity
        )
        db.session.add(copy)

    db.session.commit()

    flash("Thêm sách thành công", "success")
    return redirect(url_for("admin_bp.admin_dashboard"))
# ================== UPDATE BOOK ==================
def update_book(book_id):
    book = Book.query.get_or_404(book_id)

    title = request.form.get("title")
    isbn = request.form.get("isbn")
    category_id = request.form.get("category_id")
    publisher_id = request.form.get("publisher_id")

    # ⚠️ CHẶN NULL
    if not title or not category_id or not publisher_id:
        flash("Thiếu dữ liệu sách", "error")
        return redirect(url_for("book.admin_book_list"))

    book.title = title
    book.isbn = isbn
    book.category_id = int(category_id)
    book.publisher_id = int(publisher_id)

    db.session.commit()

    flash("Cập nhật sách thành công", "success")
    return redirect(url_for("admin_bp.admin_dashboard"))


def update_book_copy(copy_id):
    copy = BookCopy.query.get_or_404(copy_id)

    copy.branch_id = int(request.form.get("branch_id"))
    copy.shelf_location = request.form.get("shelf_location")

    copy.total_quantity = int(request.form.get("total_quantity") or 0)
    copy.available_quantity = int(request.form.get("available_quantity") or 0)

    if copy.branch_id:
        copy.branch_id = int(copy.branch_id)

    db.session.commit()

    flash("Cập nhật chi nhánh thành công", "success")

    # 👉 QUAN TRỌNG: reload admin dashboard
    return redirect(url_for("admin_bp.admin_dashboard"))

def create_book_copy(book_id):
    book = Book.query.get_or_404(book_id)

    branch_id = request.form.get("branch_id")
    shelf_location = request.form.get("shelf_location")
    total_quantity = int(request.form.get("total_quantity") or 0)

    if not branch_id:
        flash("Thiếu chi nhánh", "error")
        return redirect(url_for("book.admin_book_list"))

    # check trùng copy (1 book - 1 branch)
    existing = BookCopy.query.filter_by(
        book_id=book.id,
        branch_id=int(branch_id)
    ).first()

    if existing:
        flash("Chi nhánh này đã tồn tại cho sách", "error")
        return redirect(url_for("book.admin_book_list"))

    copy = BookCopy(
        book_id=book.id,
        branch_id=int(branch_id),
        shelf_location=shelf_location,
        total_quantity=total_quantity,
        available_quantity=total_quantity
    )

    db.session.add(copy)
    db.session.commit()

    flash("Thêm chi nhánh thành công", "success")
    return redirect(url_for("admin_bp.admin_dashboard"))

# ================== DELETE BOOK ==================
def delete_book(book_id):
    book = Book.query.get(book_id)

    if not book:
        flash("Không tìm thấy sách", "error")
        return redirect(url_for("admin_bp.admin_dashboard"))

    # 👉 xóa copies trước
    for copy in book.copies:
        db.session.delete(copy)

    db.session.delete(book)
    db.session.commit()

    flash("Xóa sách thành công", "success")
    return redirect(url_for("admin_bp.admin_dashboard"))
