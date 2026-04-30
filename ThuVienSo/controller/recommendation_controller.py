from collections import defaultdict

from flask import render_template, session
from flask_login import current_user
from sqlalchemy.orm import joinedload

from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.book_view import BookView
from ThuVienSo.data.models.borrow_prediction import BorrowPrediction
from ThuVienSo.data.models.borrow_record import BorrowRecord
from ThuVienSo.data.models.borrow_record_item import BorrowRecordItem
from ThuVienSo.data.models.favorite_category import FavoriteCategory
from ThuVienSo.data.models.recommendation import Recommendation
from ThuVienSo.data.models.search_history import SearchHistory
from ThuVienSo.data.models.user import User
from ThuVienSo.controller.book_controller import attach_books_quantity, get_user_borrow_states


def _current_user_from_session():
    if current_user and current_user.is_authenticated:
        return current_user

    user_id = session.get("user_id") or session.get("_user_id")
    if user_id:
        return User.query.get(int(user_id))

    username = session.get("username")
    if username:
        return User.query.filter_by(username=username).first()

    return None


def _base_book_query():
    return Book.query.options(
        joinedload(Book.authors),
        joinedload(Book.category),
        joinedload(Book.publisher),
        joinedload(Book.copies).joinedload(BookCopy.branch),
    )


def _latest_predictions(book_ids):
    if not book_ids:
        return {}

    rows = (
        BorrowPrediction.query
        .filter(BorrowPrediction.book_id.in_(book_ids))
        .order_by(BorrowPrediction.generated_at.desc())
        .all()
    )

    predictions = {}
    for row in rows:
        predictions.setdefault(row.book_id, row)

    return predictions


def _fallback_recommendations(user):
    scores = defaultdict(float)
    reasons = defaultdict(list)

    favorites = FavoriteCategory.query.filter_by(user_id=user.id).all()
    for item in favorites:
        books = _base_book_query().filter(Book.category_id == item.category_id).all()
        for book in books:
            scores[book.id] += float(item.score or 0) * 60
            reasons[book.id].append("Phù hợp với thể loại bạn quan tâm")

    viewed_book_ids = [
        item.book_id
        for item in BookView.query.filter_by(user_id=user.id).all()
    ]

    if viewed_book_ids:
        viewed_books = _base_book_query().filter(Book.id.in_(viewed_book_ids)).all()
        viewed_category_ids = {book.category_id for book in viewed_books}

        for category_id in viewed_category_ids:
            books = _base_book_query().filter(Book.category_id == category_id).all()
            for book in books:
                scores[book.id] += 12
                reasons[book.id].append("Gần với sách bạn đã xem")

    borrowed_items = (
        BorrowRecordItem.query
        .join(BorrowRecord)
        .filter(BorrowRecord.user_id == user.id)
        .all()
    )
    borrowed_book_ids = {item.book_id for item in borrowed_items}

    for item in borrowed_items:
        book = _base_book_query().filter(Book.id == item.book_id).first()
        if not book:
            continue

        related = _base_book_query().filter(Book.category_id == book.category_id).all()
        for related_book in related:
            scores[related_book.id] += 18
            reasons[related_book.id].append("Cùng nhóm với sách bạn từng mượn")

    keywords = [
        item.keyword.lower()
        for item in SearchHistory.query.filter_by(user_id=user.id).all()
        if item.keyword
    ]

    if keywords:
        books = _base_book_query().all()
        for book in books:
            haystack = " ".join([
                book.title or "",
                book.description or "",
                book.category.name if book.category else "",
            ]).lower()

            if any(term in haystack for keyword in keywords for term in keyword.split()):
                scores[book.id] += 8
                reasons[book.id].append("Gần với nội dung bạn đã tìm kiếm")

    for book_id in borrowed_book_ids:
        scores[book_id] -= 25

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:8]
    book_ids = [book_id for book_id, _score in ranked]
    books = _base_book_query().filter(Book.id.in_(book_ids)).all()
    books_by_id = {book.id: book for book in books}

    result = []
    for book_id, score in ranked:
        book = books_by_id.get(book_id)
        if not book:
            continue

        result.append({
            "book": book,
            "score": min(round(score / 100, 2), 0.99),
            "reason": "; ".join(dict.fromkeys(reasons[book_id])) or "Phù hợp với lịch sử đọc của bạn",
        })

    return result


def get_recommendations():
    user = _current_user_from_session()

    if not user:
        return render_template(
            "books/recommendations.html",
            recommendations=[],
            predictions={},
            user_borrow_states={},
            needs_login=True,
        )

    stored = (
        Recommendation.query
        .options(joinedload(Recommendation.book).joinedload(Book.authors))
        .options(joinedload(Recommendation.book).joinedload(Book.category))
        .options(joinedload(Recommendation.book).joinedload(Book.publisher))
        .options(joinedload(Recommendation.book).joinedload(Book.copies).joinedload(BookCopy.branch))
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.score.desc(), Recommendation.generated_at.desc())
        .all()
    )

    if stored:
        recommendations = [
            {
                "book": item.book,
                "score": item.score or 0,
                "reason": item.reason or "Phù hợp với lịch sử xem, mượn và tìm kiếm của bạn",
            }
            for item in stored
            if item.book
        ]
    else:
        recommendations = _fallback_recommendations(user)

    books = [item["book"] for item in recommendations]
    attach_books_quantity(books)
    predictions = _latest_predictions([book.id for book in books])

    return render_template(
        "books/recommendations.html",
        recommendations=recommendations,
        predictions=predictions,
        user_borrow_states=get_user_borrow_states(),
        needs_login=False,
    )
