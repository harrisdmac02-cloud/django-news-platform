# Django News Platform

Modern Django-based news publishing platform with role-based access and social features.

**Key Features**
- Role-based access: Readers, Journalists, Editors
- Publisher-managed articles + independent journalist articles
- Article submission → pending → editor approval/rejection → publish workflow
- Personalized reader feed (subscribed publishers + followed journalists)
- Newsletter creation and publishing (by journalists)
- REST API endpoints (using Django REST Framework)
- Email notifications to subscribers/followers on article publish
- Optional auto-posting to X (Twitter) when articles are published

## Prerequisites

- **Python** 3.10 – 3.12 (recommended: latest patch of 3.12 or 3.13)
- **MariaDB** 10.11+ or **MySQL** 8.0+ (MariaDB is fully compatible and recommended)
- Git
- Recommended: use of virtual environments (`venv`, `virtualenv`, or `uv`)

**Note for novices:** This guide is step-by-step. Follow exactly in order. If something fails, check error messages and prerequisites. On Windows, use Command Prompt or PowerShell; on macOS/Linux, use Terminal.

## Step-by-Step Setup Instructions

1. **Clone the repository**
   - Open your terminal/command prompt.
   - Run:
     ```bash
     git clone https://github.com/harrisdmac02-cloud/Django news_project.git
     cd Django news_project
     ```

2. **Create and activate a virtual environment** (isolates dependencies)
   - Run:
     ```bash
     python -m venv venv  # Creates a folder called 'venv'
     ```
   - Activate it:
     - On Windows: `venv\Scripts\activate`
     - On macOS/Linux: `source venv/bin/activate`
   - Your prompt should now show `(venv)` — this means it's active.

3. **Install dependencies**
   - The project requires specific Python packages. Create a `requirements.txt` file in the project root (if not present) with this content:
     ```
     django==6.0
     python-decouple>=3.8
     pillow>=10.0
     requests>=2.28
     django-environ>=0.11.2
     django-widget-tweaks>=1.5
     djangorestframework==3.15.0
     tweepy==4.14.0
     mysqlclient==2.2.4
     ```
   - Then install:
     ```bash
     pip install -r requirements.txt
     ```
   - **Note:** If `mysqlclient` fails to install (common on Windows/macOS), you may need MySQL development libraries:

     - Windows: Install MySQL Connector/C from mysql.com
     - macOS: `brew install mysql` (if using Homebrew)
     - Linux: `sudo apt install libmysqlclient-dev` (Ubuntu) or equivalent

   - If issues persist, see SQLite alternative below.

  ### Ensure SITE_ID is set

  Open `settings.py` and verify/add this line (usually near the top or bottom):

  ```python
  SITE_ID = 1

4. **Set up the database**
   - This project uses **MySQL / MariaDB** by default.

   -  Make sure MySQL or MariaDB is installed and running on your computer.
   **Windows**: Most people use **XAMPP** → start the MySQL module from the XAMPP Control Panel
   **macOS**: `brew services start mariadb` (if installed via Homebrew)
   **Ubuntu/Linux**: `sudo systemctl start mariadb` or `sudo service mariadb start`

   - Open a terminal/command prompt and log in to MySQL/MariaDB:
   ```bash
     mysql -u root -p
     ```

5. **Apply database migrations**
   - Run:
     ```bash
     python manage.py makemigrations
     python manage.py migrate
     ```
   - This sets up the database tables. If errors occur, check your `DATABASES` settings.

6. **Create a superuser** (for admin access)
   - Run:
     ```bash
     python manage.py createsuperuser
     ```
   - Follow prompts: Enter username, email (optional), password.
   - This user can access /admin/ later.

7. **Configure X (Twitter) API** (optional, but required for auto-tweeting)
   - Sign up for a developer account at https://developer.twitter.com.
   - Create an app with **Read + Write** permissions.
   - Get your API keys/tokens.
   - Update `Django news_project/settings.py`:
     ```python
     X_CONSUMER_KEY = 'your_consumer_key'
     X_CONSUMER_SECRET = 'your_consumer_secret'
     X_ACCESS_TOKEN = 'your_access_token'
     X_ACCESS_TOKEN_SECRET = 'your_access_token_secret'
     AUTO_TWEET_ENABLED = True  # Enable tweeting
     ```
   - **Security:** Never commit these to git! Use a `.env` file in production.

8. **Run the development server**
   - Run:
     ```bash
     python manage.py runserver
     ```
   - Open http://127.0.0.1:8000/ in your browser.
   - The app should load! Register a user, test features.
   - To stop: Ctrl+C in terminal.

9. **Test key features**
  - Register as Reader → subscribe to publishers, follow journalists
  - Register as Journalist → create articles/newsletters
  - Register as Editor → approve articles
  - Check personalized feed at /my-feed/
  - Verify email notifications (console backend by default)


## File Cleanup Notes
- **Remove blank/unnecessary files:** If there's a blank `requirements.txt` in the root or `Django news_project/` folder, delete it (we created a new one in step 3). No duplicates were found in the provided files, but ensure no extra `db.sqlite3` exists (add to `.gitignore` as per previous advice).
- **Add `.gitignore` (if missing):** Create in root with at least: