# Masterblog API - Steps Done

This file documents every step of the Codio guide "Masterblog API" that was
implemented in `backend/backend_app.py`, what was done and how.
Each step has its own git commit.

The backend is a Flask app that stores blog posts in an in-memory list `POSTS`.
Every post is a dictionary with an integer `id`, a `title` and a `content`.
Run it with:

```bash
python3 backend/backend_app.py   # serves on http://localhost:5002
```

---

## Step 1 - "List" endpoint (`GET /api/posts`)

**What:** The list endpoint was already provided by the course. It returns all
posts from the hardcoded `POSTS` list as JSON.

**How:** No code changes were necessary. I checked that the route
`@app.route('/api/posts', methods=['GET'])` returns `jsonify(POSTS)` and created
this `steps_done.md` file to document the following steps.

**Test:**
```bash
curl http://localhost:5002/api/posts
```
---

## Step 2 - "Add" endpoint (`POST /api/posts`)

**What:** Clients can create a new post by sending `{"title": ..., "content": ...}`.
The response is the new post (including its generated id) with status `201 Created`.

**How:**
- Imported `request` from Flask to read the JSON body
  (`request.get_json(silent=True)`, so an invalid/missing body does not crash
  but is treated as empty).
- Added the helper `generate_new_id()`, which returns the highest existing id + 1
  (or 1 if the list is empty). This always yields a **unique integer**, which the
  frontend requires - even after posts were deleted.
- Validation: if `title` and/or `content` are missing or empty, the endpoint returns
  `400 Bad Request` with a JSON error that names the missing field(s), e.g.
  `{"error": "Missing required field(s): content"}`.

**Test:**
```bash
curl -X POST http://localhost:5002/api/posts -H "Content-Type: application/json" \
     -d '{"title": "My post", "content": "Hello"}'          # -> 201
curl -X POST http://localhost:5002/api/posts -H "Content-Type: application/json" \
     -d '{"title": "Only a title"}'                         # -> 400
```
---

## Step 3 - "Delete" endpoint (`DELETE /api/posts/<id>`)

**What:** Deletes the post with the given id and returns
`{"message": "Post with id <id> has been deleted successfully."}` with `200 OK`.
If the id does not exist, it returns `404 Not Found` with an error message.

**How:**
- Added the helper `find_post_by_id(post_id)`, which loops over `POSTS` and
  returns the matching post or `None`. It is reused by the update endpoint.
- The route uses the converter `<int:post_id>`, so Flask passes the id as an
  integer (non-numeric ids automatically give a 404).
- The post is removed with `POSTS.remove(post)`.

**Test:**
```bash
curl -X DELETE http://localhost:5002/api/posts/1    # -> 200
curl -X DELETE http://localhost:5002/api/posts/999  # -> 404
```
---

## Step 4 - "Update" endpoint (`PUT /api/posts/<id>`)

**What:** Updates `title` and/or `content` of an existing post. Both fields are
optional - fields that are not sent keep their current value. Returns the
updated post with `200 OK`, or `404 Not Found` if the id does not exist.

**How:**
- Looks up the post with `find_post_by_id()`.
- Reads the JSON body and only overwrites the keys that are present
  (`if "title" in data: ...`). Because the dictionary in `POSTS` is modified
  in place, the change is visible immediately in `GET /api/posts`.

**Test:**
```bash
curl -X PUT http://localhost:5002/api/posts/2 -H "Content-Type: application/json" \
     -d '{"title": "New title"}'                            # -> 200, content unchanged
curl -X PUT http://localhost:5002/api/posts/999 -H "Content-Type: application/json" \
     -d '{"title": "x"}'                                    # -> 404
```
---

## Step 5 - "Search" endpoint (`GET /api/posts/search`)

**What:** Searches posts by the query parameters `title` and/or `content`.
Returns all posts whose title contains the `title` term **or** whose content
contains the `content` term. If nothing matches, an empty list `[]` is returned
(no special error handling needed).

**How:**
- Reads the parameters with `request.args.get(...)` (GET request, no body).
- The search is **case-insensitive** (`.lower()` on both sides) and matches
  substrings (`term in text`).
- If no search term is given at all, the endpoint returns `[]`.

**Test:**
```bash
curl "http://localhost:5002/api/posts/search?title=first"
curl "http://localhost:5002/api/posts/search?content=second"
curl "http://localhost:5002/api/posts/search?title=doesnotexist"   # -> []
```
---

## Step 6 - Sorting for the "List" endpoint (`GET /api/posts?sort=...&direction=...`)

**What:** The list endpoint accepts the optional query parameters
`sort` (`title` or `content`) and `direction` (`asc` or `desc`).
Without parameters the posts are returned in their original order, exactly as before.
Invalid values return `400 Bad Request` with an error message.

**How:**
- Added the constants `SORT_FIELDS = ("title", "content")` and
  `SORT_DIRECTIONS = ("asc", "desc")` for validation.
- If neither parameter is given, `POSTS` is returned unchanged.
- If only `sort` is given, `direction` defaults to `asc`.
- Sorting uses `sorted(POSTS, key=..., reverse=...)`, which returns a **new**
  list, so the original order in `POSTS` is not changed. The key uses `.lower()`
  so the sorting is case-insensitive.

**Test:**
```bash
curl "http://localhost:5002/api/posts?sort=title&direction=desc"
curl "http://localhost:5002/api/posts?sort=content&direction=asc"
curl "http://localhost:5002/api/posts?sort=author"        # -> 400
curl "http://localhost:5002/api/posts?sort=title&direction=up"  # -> 400
```
