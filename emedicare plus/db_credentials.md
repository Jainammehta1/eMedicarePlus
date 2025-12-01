# Database Credentials (for local development)

This file documents the database connection used by the local Python backend. The user requested the DB name/credentials stored in a `.md` file.

- Host: `localhost` (127.0.0.1)
- Port: `3306`
- Database: `emedicare`
- Username: `root`
- Password: `root`

Important: storing plaintext credentials in a repo or a markdown file is insecure. For a production system, move credentials to environment variables or a secrets manager.

How to run the backend (quick):

1. Create a Python virtualenv and install dependencies:

```powershell
cd "d:\emedicare plus\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Ensure MySQL is running and accessible on `localhost:3306` and that the `root` user has password `root`.

3. Start the Flask app:

```powershell
python app.py
```

The app will initialize the `emedicare` database and a `patients` table automatically on first run.

API endpoint used by frontend:

- `POST http://localhost:5000/signup`
  - JSON body: `{ "email": "user@example.com", "password": "secret", "role": "patient" }`
  - Successful response: `{ "success": true, "message": "Patient registered." }` (HTTP 201)

If you want the backend to listen on a different host/port or different DB credentials, update `backend/app.py` DB_CONFIG or prefer using environment variables in a future change.
