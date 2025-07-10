PixelFlow-comms

PixelFlow-comms is a real-time communication platform built with Django and Django REST Framework, designed to facilitate structured discussions within categories and topics. It includes features for user management, role-based permissions (admin), and real-time messaging.

Features
User Authentication & Authorization: Secure user registration, login, and admin roles.

Category Management: Create, view, and manage discussion categories.

Topic Management: Create, view, and manage topics within categories.

Real-time Messaging: Send and receive messages within selected topics.

Permissions & Restrictions:

Admins can manage categories, topics, and user restrictions.

Category and topic-level view/reply restrictions for users.

Dashboard: A dynamic single-page application (SPA) like interface for seamless communication.

Responsive Design: Optimized for various screen sizes.

Technologies Used
Backend: Django, Django REST Framework (DRF)

Frontend: HTML, CSS (Bootstrap), JavaScript (Vanilla JS for dynamic interactions)

Database: SQLite (default for development, can be configured for PostgreSQL/MySQL)

Version Control: Git

Getting Started
Follow these instructions to get a copy of the project up and running on your local machine for development and testing purposes.

Prerequisites
Before you begin, ensure you have the following installed:

Python 3.8+: Download Python

pip: Python package installer (usually comes with Python)

Git: Download Git

Installation
Clone the repository:

git clone https://github.com/zeesh425/PixelFlow-comms.git
cd PixelFlow-comms

Create and activate a virtual environment:

It's highly recommended to use a virtual environment to manage project dependencies.

On Windows:

python -m venv venv
.\venv\Scripts\activate

On macOS/Linux:

python3 -m venv venv
source venv/bin/activate

Install dependencies:

Install all required Python packages using pip:

pip install -r requirements.txt

Apply database migrations:

This will create the necessary database tables.

python manage.py migrate

Create a superuser (admin account):

You'll need an admin account to access the Django admin panel and manage categories/users.

python manage.py createsuperuser

Follow the prompts to set up your username, email, and password.

Run the development server:

python manage.py runserver

The application will now be running at http://127.0.0.1:8000/.

Usage
Access the Dashboard:
Open your browser and navigate to http://127.00.1:8000/users/dashboard/.

Login/Register:

If you created a superuser, you can log in directly.

New users can register via the /users/register/ endpoint (if enabled) or be created by an admin.

Admin Features:

Access the Django admin panel at http://127.0.0.1:8000/admin/ using your superuser credentials.

Here you can manage CustomUser accounts, Category, Topic, Message, CategoryRestriction, and TopicRestriction models.

Communication:

From the dashboard, create new categories and topics (if you are an admin).

Select a topic from the left sidebar to view messages and send new ones.

API Endpoints (Brief)
The project exposes a RESTful API for managing categories, topics, messages, and restrictions.

/api/topics/categories/

/api/topics/topics/

/api/conversations/messages/

/api/topics/category-restrictions/

/api/topics/topic-restrictions/

For detailed API usage, refer to the urls.py, views.py, and serializers.py files within the topics and conversations apps.

Contributing
If you'd like to contribute, please follow these steps:

Fork the repository.

Create a new branch (git checkout -b feature/your-feature-name).

Make your changes.

Commit your changes (git commit -m 'Add new feature').

Push to the branch (git push origin feature/your-feature-name).

Open a Pull Request.

License
This project is licensed under the MIT License - see the LICENSE file for details.
