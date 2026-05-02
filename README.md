# Chat-Exchange-Open

A language exchange platform for connecting learners worldwide.

![Chat-Exchange Platform](screenshot.png)

## Features

- User registration and authentication
- Language partner matching
- Real-time messaging
- Discussion forums
- Multi-language support (English/Chinese)

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JavaScript
- **Authentication**: Flask-Login

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure your environment variables:
   - `SECRET_KEY`: Flask secret key
   - `DATABASE_URL`: MySQL connection string
   - `SMTP_*`: Email configuration (optional)

4. Initialize the database:
   ```bash
   flask db upgrade
   ```

5. Run the application:
   ```bash
   python run.py
   ```

## Configuration

Create a `.env` file based on `.env.example`:

```env
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=0
DATABASE_URL=mysql+pymysql://user:password@host:port/database_name
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_FROM=noreply@example.com
```

## License

MIT License
