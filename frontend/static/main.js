// Function that runs once the window is fully loaded
window.onload = function() {
    // Attempt to retrieve the API base URL from the local storage
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');
    // If a base URL is found in local storage, load the posts
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

// Function to build the request URL from the search and sort controls
function buildPostsUrl(baseUrl) {
    var searchTerm = document.getElementById('search-term').value.trim();
    var searchField = document.getElementById('search-field').value;
    var sortField = document.getElementById('sort-field').value;
    var sortDirection = document.getElementById('sort-direction').value;

    var params = new URLSearchParams();

    // With a search term, use the /posts/search endpoint
    if (searchTerm) {
        // "All fields" sends the term for every field, the API matches if any field contains it
        var fields = searchField === 'all' ? ['title', 'content', 'author', 'date'] : [searchField];
        fields.forEach(field => params.append(field, searchTerm));
        return baseUrl + '/posts/search?' + params.toString();
    }

    // Without a search term, list all posts, sorted if a sort field is chosen
    if (sortField) {
        params.append('sort', sortField);
        params.append('direction', sortDirection);
        return baseUrl + '/posts?' + params.toString();
    }
    return baseUrl + '/posts';
}

// Function to sort posts in the browser (the search endpoint does not sort)
function sortPosts(posts) {
    var sortField = document.getElementById('sort-field').value;
    var sortDirection = document.getElementById('sort-direction').value;
    if (!sortField) {
        return posts;
    }

    // Dates are in the format YYYY-MM-DD, so comparing them as text keeps the right order
    var sorted = posts.slice().sort((a, b) =>
        String(a[sortField]).toLowerCase().localeCompare(String(b[sortField]).toLowerCase()));
    return sortDirection === 'desc' ? sorted.reverse() : sorted;
}

// Function to reset the search and sort controls and show all posts again
function clearSearch() {
    document.getElementById('search-term').value = '';
    document.getElementById('search-field').value = 'all';
    document.getElementById('sort-field').value = '';
    document.getElementById('sort-direction').value = 'asc';
    loadPosts();
}

// Function to fetch the posts from the API and display them on the page
function loadPosts() {
    // Retrieve the base URL from the input field and save it to local storage
    var baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);

    // Use the Fetch API to send a GET request, taking search and sort into account
    fetch(buildPostsUrl(baseUrl))
        .then(response => response.json().then(data => ({ ok: response.ok, data: data })))
        .then(result => {
            // Show errors from the API (e.g. an invalid sort value)
            if (!result.ok) {
                alert(result.data.error);
                return;
            }

            // Clear out the post container first
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = '';

            // The list endpoint already sorts, search results are sorted here
            const isSearch = document.getElementById('search-term').value.trim() !== '';
            const posts = isSearch ? sortPosts(result.data) : result.data;
            if (posts.length === 0) {
                postContainer.innerHTML = '<p class="no-posts">No posts found.</p>';
                return;
            }

            // For each post in the response, create a new post element and add it to the page
            posts.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';
                postDiv.innerHTML = `<h2>${escapeHtml(post.title)}</h2>
                <p class="post-meta">by ${escapeHtml(post.author)} · ${escapeHtml(post.date)}</p>
                <p>${escapeHtml(post.content)}</p>
                <button onclick="deletePost(${post.id})">Delete</button>`;
                postContainer.appendChild(postDiv);
            });
        })
        .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

// Function to send a POST request to the API to add a new post
function addPost() {
    // Retrieve the values from the input fields
    var baseUrl = document.getElementById('api-base-url').value;
    var postTitle = document.getElementById('post-title').value;
    var postContent = document.getElementById('post-content').value;
    var postAuthor = document.getElementById('post-author').value;
    var postDate = document.getElementById('post-date').value;

    var newPost = { title: postTitle, content: postContent, author: postAuthor };
    // The date is optional, the API defaults to today if it is not sent
    if (postDate) {
        newPost.date = postDate;
    }

    // Use the Fetch API to send a POST request to the /posts endpoint
    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPost)
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data: data })))
    .then(result => {
        // Show validation errors from the API (e.g. a missing author)
        if (!result.ok) {
            alert(result.data.error);
            return;
        }
        console.log('Post added:', result.data);
        loadPosts(); // Reload the posts after adding a new one
    })
    .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}

// Function to escape user text before inserting it as HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
}

// Function to send a DELETE request to the API to delete a post
function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    // Use the Fetch API to send a DELETE request to the specific post's endpoint
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
    .then(response => {
        console.log('Post deleted:', postId);
        loadPosts(); // Reload the posts after deleting one
    })
    .catch(error => console.error('Error:', error));  // If an error occurs, log it to the console
}
