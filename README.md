# gymgoers
GymGoers is a web application developed by Universidade Aberta students for the Laboratório de Desenvolvimento de Software subject. It is built in Python, following the MVC architecture.

# GymGoers

Social gym tracking webapp inspired by [Hevy](https://www.hevyapp.com/). Track your workouts, follow other gym-goers, build reusable training routines.

> **Status:** Early development. This fork is being developed solo as part of a UAB Laboratório de Desenvolvimento course assignment. Originally a group project (ByteUs-Group38), now continued individually.

---

## Stack

- **Backend:** Python 3.12 + Django 5.1
- **Database:** PostgreSQL 18
- **Frontend:** Django Templates (DTL) + Tailwind CSS + HTMX + Alpine.js
- **Architecture:** Monolithic (no separate frontend/backend)

## Project structure

gymgoers/
├── config/              # Django settings, root URLs, WSGI/ASGI
├── accounts/            # Custom User model + Profile + auth views
├── exercises/           # Exercise catalogue (seed data + search)
├── workouts/            # Workout tracking (the core feature)
├── routines/            # Reusable workout templates
├── social/              # Follow system + activity feed
├── docs/                # Architecture decisions, notes
├── manage.py
├── requirements.txt
└── .env.example         # Template for required env vars

---

## Local setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16+ (18 recommended) running locally on port 5432
- Git

### Installation

1. **Clone the repo:**

```bash
   git clone https://github.com/ElMarcio/gymgoers.git
   cd gymgoers
```

2. **Create and activate a virtual environment:**

```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate
```

3. **Install dependencies:**

```bash
   pip install -r requirements.txt
```

4. **Create the PostgreSQL database:**

```sql
   psql -U postgres
   CREATE DATABASE gymgoers;
   CREATE USER gymgoers_user WITH PASSWORD 'your_password_here';
   GRANT ALL PRIVILEGES ON DATABASE gymgoers TO gymgoers_user;
   ALTER DATABASE gymgoers OWNER TO gymgoers_user;
   \q
```

5. **Configure environment variables:**

   Copy `.env.example` to `.env` and fill in the values:

```bash
   cp .env.example .env
```

   Generate a new `SECRET_KEY`:

```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

6. **Run migrations and create a superuser:**

```bash
   python manage.py migrate
   python manage.py createsuperuser
```

7. **Run the development server:**

```bash
   python manage.py runserver
```

   Visit `http://127.0.0.1:8000/`. Admin is at `/admin/`.

---

## Development workflow

- **Branches:** work happens on `dev`. `main` only receives tested, stable merges.
- **Commits:** conventional-style prefixes — `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`.
- **Before every session:** `git status`, `git pull`, `python manage.py check`.

---

## Documentation

- [`docs/DECISIONS.md`](docs/DECISIONS.md) — architectural and technical decisions with rationale.

---

## License

See [LICENSE](LICENSE).