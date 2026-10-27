from datetime import date, datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post.",
     "author": "Alice", "date": "2023-06-07"},
    {"id": 2, "title": "Second post", "content": "This is the second post.",
     "author": "Bob", "date": "2023-06-10"},
]

TEXT_FIELDS = ("title", "content", "author")
POST_FIELDS = TEXT_FIELDS + ("date",)
DATE_FORMAT = "%Y-%m-%d"

SORT_FIELDS = POST_FIELDS
SORT_DIRECTIONS = ("asc", "desc")

# SWAGGER stuff
SWAGGER_URL="/api/docs"  # (1) swagger endpoint e.g. HTTP://localhost:5002/api/docs
API_URL="/static/masterblog.json" # (2) ensure you create this dir and file

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': 'Masterblog API' # (3) You can change this if you like
    }
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)


def find_post_by_id(post_id):
    """Return the post with the given id, or None if it does not exist."""
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


def generate_new_id():
    """Return a unique integer id (highest existing id + 1)."""
    return max((post["id"] for post in POSTS), default=0) + 1


def parse_date(value):
    """Return a date object for a 'YYYY-MM-DD' string, or None if invalid."""
    try:
        return datetime.strptime(value, DATE_FORMAT).date()
    except (TypeError, ValueError):
        return None


def validate_post_fields(data, required):
    """Return an error message for invalid post data, or None if it is valid.

    With required=True all text fields must be present (create);
    otherwise only the provided fields are checked (update).
    """
    if not isinstance(data, dict):
        return "Request body must be a JSON object."

    if required:
        missing_fields = [field for field in TEXT_FIELDS
                          if field not in data]
        if missing_fields:
            return f"Missing required field(s): {', '.join(missing_fields)}"

    for field in TEXT_FIELDS:
        if field in data and (not isinstance(data[field], str)
                              or not data[field].strip()):
            return f"Field '{field}' must be a non-empty string."

    if "date" in data and parse_date(data["date"]) is None:
        return "Field 'date' must be a valid date in the format YYYY-MM-DD."

    return None


def sort_key(sort_field):
    """Return a key function that sorts posts by the given field."""
    if sort_field == "date":
        # Compare real dates, not their string representation
        return lambda post: parse_date(post["date"])
    return lambda post: post[sort_field].lower()


@app.route('/api/posts', methods=['GET'])
def get_posts():
    sort_field = request.args.get('sort')
    direction = request.args.get('direction')

    # Without sort parameters, keep the original order
    if sort_field is None and direction is None:
        return jsonify(POSTS)

    if sort_field not in SORT_FIELDS:
        return jsonify({
            "error": f"Invalid sort field '{sort_field}'. "
                     f"Allowed values: {', '.join(SORT_FIELDS)}."
        }), 400

    direction = (direction or "asc").lower()
    if direction not in SORT_DIRECTIONS:
        return jsonify({
            "error": f"Invalid sort direction '{direction}'. "
                     f"Allowed values: {', '.join(SORT_DIRECTIONS)}."
        }), 400

    sorted_posts = sorted(
        POSTS,
        key=sort_key(sort_field),
        reverse=(direction == "desc"),
    )
    return jsonify(sorted_posts)


@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.get_json(silent=True) or {}

    error = validate_post_fields(data, required=True)
    if error:
        return jsonify({"error": error}), 400

    # Date is optional and defaults to today
    post_date = parse_date(data["date"]) if "date" in data else date.today()

    new_post = {
        "id": generate_new_id(),
        "title": data["title"],
        "content": data["content"],
        "author": data["author"],
        "date": post_date.strftime(DATE_FORMAT),
    }
    POSTS.append(new_post)
    return jsonify(new_post), 201


@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404

    POSTS.remove(post)
    return jsonify({
        "message": f"Post with id {post_id} has been deleted successfully."
    }), 200


@app.route('/api/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    post = find_post_by_id(post_id)
    if post is None:
        return jsonify({"error": f"Post with id {post_id} was not found."}), 404

    data = request.get_json(silent=True) or {}

    error = validate_post_fields(data, required=False)
    if error:
        return jsonify({"error": error}), 400

    # Only overwrite the fields that were provided, keep the rest
    for field in TEXT_FIELDS:
        if field in data:
            post[field] = data[field]
    if "date" in data:
        # Store the date normalized, e.g. "2023-6-7" -> "2023-06-07"
        post["date"] = parse_date(data["date"]).strftime(DATE_FORMAT)

    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    queries = {
        field: request.args.get(field, '').strip().lower()
        for field in POST_FIELDS
    }
    queries = {field: query for field, query in queries.items() if query}

    # No search terms -> nothing to match
    if not queries:
        return jsonify([])

    # A post matches if any of the given fields contains its search term
    results = [
        post for post in POSTS
        if any(query in post[field].lower()
               for field, query in queries.items())
    ]
    return jsonify(results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
