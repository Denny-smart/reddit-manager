# 📌 Reddit Manager

A **Reddit Post Manager** that enables users to authenticate their Reddit accounts, create and schedule posts, and manage multiple accounts from a single platform.  
It simplifies subreddit posting, saves time, and provides better account and post management. 

## 🚀 Live URLs

- **Frontend:** https://reddit-sync-dash.vercel.app/
- **Backend API:** https://reddit-manager.onrender.com


---

## 🌟 Features

- **User Authentication** → Secure signup, login, and logout with **JWT & OAuth2.0**  
- **Reddit Account Integration** → Connect and manage multiple Reddit accounts via **Auth0 & Reddit API (PRAW)**  
- **Post Management** → Create, edit, delete, and schedule posts to specific subreddits  
- **Post Tracking** → View and track posts published across connected Reddit accounts  

---

## 🏗️ Tech Stack

- **Frontend:** React, HTML, CSS, Typescript 
- **Backend:** Python, Django, Django REST Framework (DRF)  
- **Database:** PostgreSQL
- **Authentication:** Django Auth, JWT, OAuth2.0
- **Deployment:** 
  - Frontend: Vercel
  - Backend: Render
  - Database: PostgreSQL (Render) 

---

## 🔗 API Endpoints

Base URL:  
https://reddit-manager.onrender.com

### 🔑 Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/auth/signup/` | Register a new user |
| POST   | `/api/auth/login/` | Authenticate and log in a user |
| POST   | `/api/auth/logout/` | Log out the current user |
| GET    | `/api/auth/user/` | Get current user info |
| POST   | `/api/token/` | Obtain JWT token |
| POST   | `/api/token/refresh/` | Refresh JWT token |

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
| GET    | `/api/posts/` | List all posts for logged-in user |
| POST   | `/api/posts/create/` | Create new post |
| GET    | `/api/posts/<id>/` | Get specific post details |
| PUT    | `/api/posts/<id>/` | Update existing post |
| DELETE | `/api/posts/<id>/` | Delete a post |
| GET    | `/api/posts/posted/` | View published posts |
| GET    | `/api/posts/scheduled/` | View scheduled posts |
| POST   | `/api/posts/<id>/publish/` | Publish a specific post |
| POST   | `/api/posts/<id>/schedule/` | Schedule a post |

### 🔍 Health Check
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/health/` | Check API health status |

> Note: All endpoints except `/health/` and authentication endpoints require JWT authentication via `Authorization: Bearer <token>` header.
---

## 💻 Local Development Setup

### Requirements

- Python 3.10+
- PostgreSQL

---

### Backend Setup

1. **Clone the repository:**
   ```bash
   https://github.com/Denny-smart/reddit-manager.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd reddit-manager
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

4. **Activate the virtual environment:**
   ```bash
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

7. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

> **Note:** The server will be running at http://127.0.0.1:8000/

---

## 🔑 Reddit API Setup

### 1. Create a Reddit App

1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click **"create another app..."**
3. Fill in the following details:
   - **Name:** `Reddit Manager` (or your preferred name)
   - **Type:** Select `web app`
   - **Description:** Brief description of your app
   - **About URL:** Your project URL (optional)
   - **Redirect URI:** `http://localhost:8000/api/reddit/callback/`
4. Click **"create app"**

### 2. Get Your Credentials

After creating the app, note down:
- **Client ID:** Found under your app name (e.g., `YourAppID`)
- **Client Secret:** Listed as 'secret'

### 3. Configure Environment Variables

Create a `.env` file in your project root directory:

```env
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=script:RedditManager:v1.0 (by /u/your_username)
REDDIT_REDIRECT_URI=http://localhost:8000/api/reddit/callback/
```

### 4. Test Your Setup

1. **Start your server:**
   ```bash
   python manage.py runserver
   ```

2. **Visit the connection endpoint:**
   ```
   http://localhost:8000/api/reddit/connect/
   ```

3. **Verify:** You should be redirected to Reddit's OAuth consent screen
   

> **📝 Note: You need to be logged into your application to connect a Reddit account.

> **⚠️ Important:** Never commit your `.env` file or share your Reddit API credentials publicly.

---

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
