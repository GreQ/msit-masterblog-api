from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]

SORT_FIELDS = ("title", "content")
SORT_DIRECTIONS = ("asc", "desc")


def find_post_by_id(post_id):
    """Return the post with the given id, or None if it does not exist."""
    for post in POSTS:
        if post["id"] == post_id:
            return post
    return None


def generate_new_id():
    """Return a unique integer id (highest existing id + 1)."""
    return max((post["id"] for post in POSTS), default=0) + 1


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
        key=lambda post: post[sort_field].lower(),
        reverse=(direction == "desc"),
    )
    return jsonify(sorted_posts)


@app.route('/api/posts', methods=['POST'])
def add_post():
    data = request.get_json(silent=True) or {}

    missing_fields = [field for field in ("title", "content")
                      if not str(data.get(field) or "").strip()]
    if missing_fields:
        return jsonify({
            "error": f"Missing required field(s): {', '.join(missing_fields)}"
        }), 400

    new_post = {
        "id": generate_new_id(),
        "title": data["title"],
        "content": data["content"],
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
    # Only overwrite the fields that were provided, keep the rest
    if "title" in data:
        post["title"] = data["title"]
    if "content" in data:
        post["content"] = data["content"]

    return jsonify(post), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    title_query = request.args.get('title', '').strip().lower()
    content_query = request.args.get('content', '').strip().lower()

    # No search terms -> nothing to match
    if not title_query and not content_query:
        return jsonify([])

    results = [
        post for post in POSTS
        if (title_query and title_query in post["title"].lower())
        or (content_query and content_query in post["content"].lower())
    ]
    return jsonify(results)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
