from collections import defaultdict

from flask import render_template, session
from flask_login import current_user
from sqlalchemy.orm import joinedload

from ThuVienSo.data.models.book import Book
from ThuVienSo.data.models.book_copy import BookCopy
from ThuVienSo.data.models.book_view import BookView
from ThuVienSo.data.models.borrow_prediction import BorrowPrediction
from ThuVienSo.data.models.borrow_request import BorrowRequest
from ThuVienSo.data.models.borrow_request_item import BorrowRequestItem
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
    return (
        Book.query
        .filter(Book.is_deleted == False)
        .options(
            joinedload(Book.authors),
            joinedload(Book.category),
            joinedload(Book.publisher),
            joinedload(Book.copies).joinedload(BookCopy.branch),
        )
    )


def _role_name(user):
    return (user.role.name if user and user.role else "").strip().lower()


def _is_manager(user):
    return _role_name(user) in {
        "admin",
        "quản trị",
        "quản trị viên",
        "quan tri",
        "quan tri vien",
        "thủ thư",
        "thu thu",
        "librarian",
    }


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


def _user_has_recommendation_history(user):
    if not user:
        return False

    if FavoriteCategory.query.filter_by(user_id=user.id).first():
        return True

    if BookView.query.filter_by(user_id=user.id).first():
        return True

    if SearchHistory.query.filter_by(user_id=user.id).first():
        return True

    borrowed = (
        BorrowRecordItem.query
        .join(BorrowRecord)
        .filter(BorrowRecord.user_id == user.id)
        .first()
    )

    return bool(borrowed)


def _general_reader_recommendations(limit=8):
    scores = defaultdict(float)

    for item in BookView.query.all():
        scores[item.book_id] += 1

    for item in BorrowRecordItem.query.all():
        scores[item.book_id] += 3 * (item.quantity or 1)

    pending_items = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(BorrowRequest.status.in_(["pending", "approved"]))
        .all()
    )

    for item in pending_items:
        scores[item.book_id] += 2 * (item.quantity or 1)

    if scores:
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
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
                "reason": "",
            })

            if len(result) >= limit:
                return result

        if result:
            return result

    books = (
        _base_book_query()
        .order_by(Book.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "book": book,
            "score": 0,
            "reason": "",
        }
        for book in books
    ]


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


def _manager_recommendations():
    scores = defaultdict(float)
    reasons = defaultdict(list)

    for item in BookView.query.all():
        scores[item.book_id] += 1
        reasons[item.book_id].append("được độc giả xem nhiều")

    for item in BorrowRecordItem.query.all():
        scores[item.book_id] += 3 * (item.quantity or 1)
        reasons[item.book_id].append("có lịch sử mượn thực tế")

    pending_items = (
        BorrowRequestItem.query
        .join(BorrowRequest)
        .filter(BorrowRequest.status.in_(["pending", "approved"]))
        .all()
    )

    for item in pending_items:
        scores[item.book_id] += 2 * (item.quantity or 1)
        reasons[item.book_id].append("đang có nhu cầu/yêu cầu mượn")

    favorites = FavoriteCategory.query.all()
    favorite_category_scores = defaultdict(float)
    for item in favorites:
        favorite_category_scores[item.category_id] += float(item.score or 0)

    if favorite_category_scores:
        books = _base_book_query().all()
        for book in books:
            if book.category_id in favorite_category_scores:
                scores[book.id] += favorite_category_scores[book.category_id] * 2
                reasons[book.id].append("thuộc thể loại độc giả quan tâm")

    searches = [item.keyword.lower() for item in SearchHistory.query.all() if item.keyword]
    if searches:
        books = _base_book_query().all()
        for book in books:
            haystack = " ".join([
                book.title or "",
                book.description or "",
                book.category.name if book.category else "",
            ]).lower()

            matches = sum(
                1
                for keyword in searches
                if any(term in haystack for term in keyword.split())
            )

            if matches:
                scores[book.id] += matches * 1.5
                reasons[book.id].append("khớp với xu hướng tìm kiếm")

    books = _base_book_query().filter(Book.id.in_(scores.keys())).all() if scores else []
    attach_books_quantity(books)
    predictions = _latest_predictions([book.id for book in books])

    result = []
    for book in books:
        prediction = predictions.get(book.id)
        available = getattr(book, "available_quantity", 0) or 0
        predicted = prediction.predicted_borrow_count if prediction else 0
        demand_score = scores[book.id] + (predicted * 1.5)
        target_stock = max(int(round(demand_score / 4)), predicted, 1)
        suggested_import_qty = max(target_stock - available, 0)

        if suggested_import_qty <= 0 and demand_score < 4:
            continue

        result.append({
            "book": book,
            "demand_score": round(demand_score, 1),
            "available": available,
            "suggested_import_qty": suggested_import_qty,
            "prediction": prediction,
            "reason": ", ".join(dict.fromkeys(reasons[book.id])) or "có tín hiệu nhu cầu từ độc giả",
        })

    return sorted(
        result,
        key=lambda item: (item["suggested_import_qty"], item["demand_score"]),
        reverse=True,
    )[:10]


def get_recommendations():
    user = _current_user_from_session()

    if not user:
        return render_template(
            "books/recommendations.html",
            recommendations=[],
            manager_recommendations=[],
            predictions={},
            user_borrow_states={},
            needs_login=True,
            is_manager=False,
        )

    if _is_manager(user):
        return render_template(
            "books/recommendations.html",
            recommendations=[],
            manager_recommendations=_manager_recommendations(),
            predictions={},
            user_borrow_states={},
            needs_login=False,
            is_manager=True,
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

    has_history = _user_has_recommendation_history(user)

    if has_history and stored:
        recommendations = [
            {
                "book": item.book,
                "score": item.score or 0,
                "reason": item.reason or "",
            }
            for item in stored
            if item.book and not item.book.is_deleted
        ]
    elif has_history:
        recommendations = _fallback_recommendations(user)
    else:
        recommendations = _general_reader_recommendations()

    if not recommendations:
        recommendations = _general_reader_recommendations()

    books = [item["book"] for item in recommendations]
    attach_books_quantity(books)
    predictions = _latest_predictions([book.id for book in books])

    return render_template(
        "books/recommendations.html",
        recommendations=recommendations,
        manager_recommendations=[],
        predictions=predictions,
        user_borrow_states=get_user_borrow_states(),
        needs_login=False,
        is_manager=False,
    )
