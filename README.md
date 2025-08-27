# 📌 Reddit Manager

A **Reddit Post Manager** that enables users to authenticate their Reddit accounts, create and schedule posts, and manage multiple accounts from a single platform.  
It simplifies subreddit posting, saves time, and provides better account and post management.

---

## 🌟 Features

- **User Authentication** → Secure signup, login, and logout with **JWT & OAuth2.0**  
- **Reddit Account Integration** → Connect and manage multiple Reddit accounts via **Auth0 & Reddit API (PRAW)**  
- **Post Management** → Create, edit, delete, and schedule posts to specific subreddits  
- **Post Tracking** → View and track posts published across connected Reddit accounts  

---

## 🏗️ Tech Stack

- **Frontend:** React (planned), HTML, CSS, JavaScript  
- **Backend:** Python, Django, Django REST Framework (DRF)  
- **Database:** SQLite (development), PostgreSQL (production-ready)  
- **Authentication:** Django Auth, JWT, OAuth2.0 (via Auth0 & Reddit API)  

---

## 🔗 API Endpoints

Base URL:  
`http://127.0.0.1:8000/`

### 🔑 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/auth/signup/` | Register a new user |
| POST   | `/api/auth/login/` | Authenticate and log in a user |
| POST   | `/api/auth/logout/` | Log out the current user |

### 🦊 Reddit Account Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/reddit/accounts/` | List all connected Reddit accounts |
| POST   | `/api/reddit/connect/` | Initiate OAuth flow to connect a Reddit account |
| GET    | `/api/reddit/callback/` | Handle the Reddit OAuth callback |
| DELETE | `/api/reddit/disconnect/<id>/` | Disconnect a specific Reddit account |

### 📝 Post Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/posts/` | Retrieve all posts for the logged-in user |
| POST   | `/api/posts/create/` | Create a new post with title, content, subreddit, and schedule |
| GET    | `/api/posts/posted/` | View already published posts |
| PUT    | `/api/posts/<id>/` | Update an existing post |
| DELETE | `/api/posts/<id>/` | Delete a post |

---

## 💻 Getting Started

### ✅ Prerequisites
- Python (3.x recommended)  
- Django  
- PRAW  

### ⚙️ Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/your_username/reddit-manager.git
2.  Navigate to the project directory:
    ```bash
    cd reddit-manager
3. Create a virtual environment:
    ```bash
    python -m venv venv
4. Activate the virtual environment:
  ```bash
   On Windows: venv\Scripts\activate
5.  Install dependencies `requirements.txt`:
  ```bash
    pip install -r requirements.txt
6.  Apply database migrations:
  ```bash
    python manage.py migrate
7. Start the development server:
  ```bash
    python manage.py runserver

* The server will be running at http://127.0.0.1:8000/.

---
