# Coderr Backend

Coderr is the backend for a freelance service marketplace. **Business** users
publish *offers* (service packages with basic, standard, and premium tiers),
**customer** users place *orders* based on those offers and leave *reviews*, and
the platform exposes aggregated statistics for its landing page.

It is a Django REST Framework API with token authentication, built to be
consumed by the Coderr frontend.

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

Create an admin user (optional, e.g. for the Django admin or order deletion):

```bash
.venv\Scripts\python.exe manage.py createsuperuser
```

Run the development server:

```bash
.venv\Scripts\python.exe manage.py runserver
```

The local API is available at `http://127.0.0.1:8000/`, and the Django admin at
`http://127.0.0.1:8000/admin/`.

## Live demo

A running instance (frontend + API) is available at
**https://coderr.friggemann.eu**. The API is served under the `/backend/` path
(e.g. `https://coderr.friggemann.eu/backend/api/base-info/`).

## Features

- **Authentication** — registration and login returning an auth token; users
  register as either a `customer` or a `business` account.
- **Profiles** — retrieve and update user profiles; list business and customer
  profiles.
- **Offers** — business users create offers with three detail tiers
  (basic/standard/premium); public, paginated listing with filtering, search,
  and ordering.
- **Orders** — customers create orders from an offer detail; business users
  update order status; order counters per business user.
- **Reviews** — customers review business users (one review per business),
  editable and deletable by their author.
- **Base info** — aggregated platform statistics (review count, average rating,
  business profile count, offer count).

The full endpoint reference lives in [docs/endpoints.md](docs/endpoints.md).

## Tech stack

- Python 3.12 or newer
- Django and Django REST Framework
- DRF token authentication
- SQLite for local development
- Ruff (lint and format) and pytest (tests and coverage)

## User types and authentication

Coderr distinguishes two account types, chosen at registration via the `type`
field:

- **customer** — can place orders and write reviews.
- **business** — can publish offers and update order statuses.

Authenticated requests send the token returned by registration or login in the
`Authorization` header:

```text
Authorization: Token <your-token>
```

Deleting an order is restricted to staff users. A token for an existing staff
user can be created with:

```bash
.venv\Scripts\python.exe manage.py drf_create_token <username>
```

## Project structure

- `core/` — Django project configuration
- `auth_app/` — registration and login
- `profiles_app/` — user profiles
- `offers_app/` — offers and offer details
- `orders_app/` — orders and order counters
- `reviews_app/` — reviews and ratings
- `base_info_app/` — aggregated platform statistics (base-info endpoint)
- `docs/` — endpoint reference and delivery checklist

## Running checks

Run Django's built-in checks:

```bash
.venv\Scripts\python.exe manage.py check
```

Run the linter and formatting check:

```bash
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format . --check
```

Run the tests with coverage:

```bash
.venv\Scripts\python.exe -m pytest
```

The coverage threshold is configured at 95% in `pyproject.toml`.

## Delivery checklist

The project requirements and definition of done are documented in
[docs/checkliste.md](docs/checkliste.md). Key requirements:

- All endpoints match the provided documentation.
- The project reaches at least 95% coverage in the project management tests.
- Code is PEP8-compliant; functions and methods keep a single responsibility.
- The backend stays in its own repository without frontend code.
- The database file is never committed.

## Repository hygiene

The local database file `db.sqlite3` is ignored by Git and must not be uploaded.
The following are not committed:

- `.env`
- `.venv/` and `venv/`
- `db.sqlite3`
- `media/` and `staticfiles/`
- IDE and local settings files
