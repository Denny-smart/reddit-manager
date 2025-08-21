Reddit Manager

Reddit Manager is a simple web project that helps users manage their Reddit activity more easily.
Instead of logging in and posting manually every time, this tool lets you connect your Reddit account and schedule or send posts through a simple interface.

Think of it like a helper app that makes posting to Reddit faster and more organized.

🌟 Features

Connect your Reddit account (securely using Reddit’s API).

Create and save posts.

Schedule posts to specific subreddits.

View posting history.

Manage multiple Reddit accounts (future upgrade).

🛠️ Technology Used

Python & Django → Backend framework

PRAW (Python Reddit API Wrapper) → To talk with Reddit

SQLite / PostgreSQL → Database to save user posts & accounts

REST API → So the app can be extended to front-ends or mobile apps

🔗 API Endpoints

Here are the main API endpoints the project will have:

🔑 Authentication

POST /api/auth/register/ → Create a new user

POST /api/auth/login/ → Login and get an access token

POST /api/auth/logout/ → Logout user

👤 Reddit Account Management

POST /api/reddit/connect/ → Connect a Reddit account (using Reddit API credentials)

GET /api/reddit/accounts/ → List connected accounts

📝 Post Management

POST /api/posts/create/ → Create a post (title, content, subreddit)

GET /api/posts/ → View all posts by the user

PUT /api/posts/{id}/ → Edit a post

DELETE /api/posts/{id}/ → Delete a post

📅 Scheduling

POST /api/schedule/ → Schedule a post to go live at a certain time

GET /api/schedule/ → View scheduled posts

🚀 Why This Project?

Reddit is powerful, but posting regularly can be time-consuming. This tool helps by giving you a single place to manage posts, accounts, and schedules — making life easier for bloggers, marketers, or anyone active on Reddit.# reddit-manager
