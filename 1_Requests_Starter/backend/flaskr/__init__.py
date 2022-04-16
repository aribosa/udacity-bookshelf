import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy  # , or_
from flask_cors import CORS
import random

from models import setup_db, Book

BOOKS_PER_SHELF = 8


# @TODO: General Instructions
#   - As you're creating endpoints, define them and then search for 'TODO' within the frontend to update the endpoints there.
#     If you do not update the endpoints, the lab will not work - of no fault of your API code!
#   - Make sure for each route that you're thinking through when to abort and with which kind of error
#   - If you change any of the response body keys, make sure you update the frontend to correspond.


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    db = setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
        )
        return response

    def paginate_results(selection, request, items_per_page=BOOKS_PER_SHELF):
        page = request.args.get('page', default=1, type=int)
        start = (page - 1) * items_per_page
        end = start + items_per_page
        return selection[start:end]

    @app.route('/books', methods=['GET'])
    def get_books():

        books = Book.query.order_by(Book.id).all()
        books = paginate_results([book.format() for book in books], request)

        if books:
            return jsonify({
                'success': True,
                'books': books,
                'results': len(books),
                'total_books': len(Book.query.all())
            })

        else:
            abort(404)

    @app.route('/books/<int:book_id>', methods=['GET', 'PATCH'])
    def book(book_id):
        book_selected = Book.query.get(book_id)
        if not book_selected:
            return jsonify({'success': False}), 404

        # GET the specific book
        if request.method == 'GET':
            return jsonify({
                'message': 'success',
                'book': book_selected.format()
            })

        # Update the book
        if request.method == 'PATCH':
            data = request.get_json()
            print(data)
            try:
                book_selected.rating = int(data['rating'])
                db.session.add(book_selected)
                db.session.commit()

            except:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'One of the given parameter was not recognized'
                }), 402
            return jsonify({'success': True, 'book': book_selected.id})

    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        book_selected = Book.query.get(book_id)
        if not book_selected:
            return jsonify({'success': False}), 404

        if book_selected:
            try:
                book_selected.delete()
                selection = Book.query.all()
                current_books = paginate_results(selection, request)
                return jsonify({
                    'success': True,
                    'deleted': book_id,
                    'books': [book.format() for book in current_books],
                    'total_books': len(Book.query.all())
                }), 200
            except:
                db.session.rollback()
                abort(500)

        else:
            return jsonify({'success': False}), 404

    # @TODO: Write a route that create a new book.
    #        Response body keys: 'success', 'created'(id of created book), 'books' and 'total_books'
    # TEST: When completed, you will be able to a new book using the form. Try doing so from the last page of books.
    #       Your new book should show up immediately after you submit it at the end of the page.
    @app.route('/books', methods=['POST'])
    def new_book():
        user_request = request.get_json()
        try:
            created_book = Book(
                title=user_request['title'],
                author=user_request.get('author', 'Unknown'),
                rating=int(user_request.get('rating'))
            )
            created_book.insert()

            selection = Book.query.order_by(Book.id).all()
            selected_books = paginate_results(selection, request)
            return jsonify({
                'success': True,
                'created': created_book.id,
                'books': [bk.format() for bk in selected_books],
                'total_books': len(Book.query.all())
            }), 200

        except Exception as error:
            print(error)
            db.session.rollback()
            return jsonify({'success': False}), 402

    return app
