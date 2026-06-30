# Coderr Backend

Coderr is a Django REST Framework backend project. The repository currently contains the base Django project configuration, API documentation, and project delivery checklists.

## Project Status

The project is in its initial backend setup phase.

Current structure:

- `core/` - Django project configuration
- `manage.py` - Django management entry point
- `requirements.txt` - Python dependencies
- `docs/checkliste.md` - project delivery checklist
- `docs/endpoints.md` - required API endpoint documentation

## Requirements

- Python 3.12 or newer
- pip
- Virtual environment support

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply database migrations:

```bash
.venv\Scripts\python.exe manage.py migrate
```

Create an admin user:

```bash
.venv\Scripts\python.exe manage.py createsuperuser
```

Run the development server:

```bash
.venv\Scripts\python.exe manage.py runserver
```

The local API is available at:

```text
http://127.0.0.1:8000/
```

The Django admin is available at:

```text
http://127.0.0.1:8000/admin/
```

## API Documentation

The required endpoints are documented in:

[docs/endpoints.md](docs/endpoints.md)

Each endpoint entry contains the expected method, path, request body, response body, status codes, permissions, and implementation checkbox.

## Delivery Checklist

The project requirements and definition of done are documented in:

[docs/checkliste.md](docs/checkliste.md)

Important requirements include:

- All endpoints must match the provided documentation.
- The final project should reach at least 95% test coverage in the project management tests.
- Code must be PEP8-compliant.
- Functions and methods should have one responsibility and stay concise.
- The backend must remain in its own repository without frontend code.
- The database file must not be committed.

## Development Notes

This project uses:

- Django
- Django REST Framework
- DRF token authentication
- SQLite for local development

The local database file `db.sqlite3` is ignored by Git and must not be uploaded to the repository.

## Running Checks

Run Django's built-in checks:

```bash
.venv\Scripts\python.exe manage.py check
```

Run the linter:

```bash
.venv\Scripts\python.exe -m ruff check .
```

Check formatting:

```bash
.venv\Scripts\python.exe -m ruff format . --check
```

Run tests with coverage:

```bash
.venv\Scripts\python.exe -m pytest
```

The coverage threshold is configured at 95% in `pyproject.toml`.

## Repository Hygiene

Do not commit:

- `.env`
- `.venv/`
- `venv/`
- `db.sqlite3`
- `media/`
- `staticfiles/`
- IDE settings
- local settings files
