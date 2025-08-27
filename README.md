# Reddit Manager

This project is a Reddit Post Manager that allows users to authenticate their Reddit accounts, create and schedule posts, and manage multiple Reddit accounts from a single platform. It simplifies the process of posting to subreddits, saving users time while ensuring better account and post management.

## 🌟 Key Features

* **Feature A:** User Authentication: Secure signup, login, and logout with JWT and OAuth2.0.
* **Feature B:** Reddit Account Integration: Connect and manage multiple Reddit accounts via Auth0 & Reddit API (PRAW).
* **Feature C:** Post Management: Create, edit, delete, and schedule posts to specific subreddits.
* **Feature D:** Post Tracking: View and track posts you’ve published across connected Reddit accounts.

## 🏗️ Technical Stack

This project is built using the following technologies and frameworks:

* **Frontend:** [React (planned), HTML, CSS, JavaScript]
* **Backend:** [Python, Django, Django REST Framework (DRF)]
* **Database:** [SQLite (development), PostgreSQL (production-ready)]
* **Authentication:** [Django Auth, JWT, OAuth 2.0 (via Auth0 & Reddit API)]

---

## 🔗 API Endpoints

This section documents the primary endpoints available in the application. All requests should be made to `[http://127.0.0.1:8000/]`.

| Category | HTTP Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |

* 🔑 Authentication

| HTTP | Method	| Endpoint	| Description |
| POST	| /api/auth/signup/	| Registers a new user. |
| POST	| /api/auth/login/	| Authenticates and logs in a user. |
| POST	| /api/auth/logout/ |	Logs out the current user. |

* 🦊 Reddit Account Management

| HTTP | Method	| Endpoint	| Description |
| GET | /api/reddit/accounts/ |	Lists all connected Reddit accounts for the logged-in user. |
| POST | /api/reddit/connect/ |	Initiates the OAuth flow to connect a new Reddit account. |
| GET |	/api/reddit/callback/ |	The callback URL for the Reddit OAuth flow. |
| DELETE |	/api/reddit/disconnect/<id>/ |	Disconnects a specific Reddit account. |

* 📝 Post Management

| HTTP | Method |	Endpoint | Description |
| GET |	/api/posts/ |	Retrieves a list of all posts for the logged-in user. |
| POST |	/api/posts/create/ |	Creates a new post with a title, content, subreddit, and a scheduled time. |
| GET |	/api/posts/posted/ |	Views posts that have already been published. |
| PUT |	/api/posts/<id>/ |	Updates an existing post. |
| DELETE |	/api/posts/<id>/ |	Deletes a post. |

---

## 💻 Getting Started

### Prerequisites

* [List any required software, e.g., Django, Python, PRAW]

### Installation

1.  Clone the repository:
    `git clone https://github.com/your_username/reddit-manager.git`
2.  Navigate to the project directory:
    `cd reddit-manager`
3. Create a virtual environment:
    `python -m venv venv`
4. Activate the virtual environment:
`On Windows: venv\Scripts\activate`

`On macOS/Linux: source venv/bin/activate`
5.  Install dependencies `requirements.txt`:
    `pip install -r requirements.txt`
6.  Apply database migrations:
    `python manage.py migrate`
7. Start the development server:
    `python manage.py runserver`

* The server will be running at http://127.0.0.1:8000/.

---
