# Architectural & Technical Decisions

This document records non-trivial technical decisions made during the development of GymGoers, along with the context and alternatives considered. It exists to:

- Remind future-me why something was built this way.
- Provide material for the final course report.
- Make it easy for reviewers to understand *why* rather than just *what*.

Each entry follows a lightweight ADR (Architecture Decision Record) format:
**Context → Decision → Consequences**.

---

## ADR-001: Continue with Django despite solo development

**Date:** 2026-04-23
**Status:** Accepted

### Context

Project originally scoped as a group of four using Django + PostgreSQL + HTMX + Alpine + Tailwind. The group became inactive. As the remaining developer, I evaluated whether to change stack (e.g., FastAPI + React, Next.js, or similar) for a solo run, given that the original choice was partly driven by group coordination needs.

### Decision

**Stay with Django.**

### Rationale

- **Goal is to deliver a course assignment in 6-8 weeks, not to maximize résumé surface area.** Switching stack mid-project would consume weeks in tooling and re-learning before any feature could be built.
- **Mobile app is only a vague future possibility.** If it were certain, API-first (DRF + separate frontend) would be justified. As it's not, monolith stays.
- **Beginner-level experience with both Django and modern JS.** Django + HTMX has a much gentler learning curve and keeps the entire feature loop (model → view → template → interaction) in one place.
- **Diagrams (UML use case, activity, class) were already produced for the Django-native design.** Discarding them would be self-sabotage.

### Consequences

- Fast iteration and minimal tooling overhead.
- Frontend expressiveness limited vs a React-based SPA, but acceptable given scope.
- If a mobile app becomes a real requirement later, adding Django REST Framework as a layer on top of existing models remains feasible.

---

## ADR-002: Custom User model from day one

**Date:** 2026-04-23
**Status:** Accepted

### Context

Django ships with a built-in `User` model that works out of the box. Django's own documentation, however, strongly recommends creating a custom user model at the start of every new project — because migrating to a custom user model after the first migration has run is notoriously painful (the user table is referenced by many others via foreign keys).

### Decision

Created `accounts.User` extending `AbstractUser`, configured `AUTH_USER_MODEL = 'accounts.User'` in settings, and dropped & recreated the local database to re-run migrations cleanly with the custom model from the first migration.

### Rationale

- The cost of creating a custom user model now (even if identical to `AbstractUser`) is near zero.
- The cost of adding one later is significant and risky.
- Likely future needs — fitness-related profile fields, alternative login flows, soft-delete — all become trivial to add when the user model is already ours to extend.

### Consequences

- Any future user-related field can be added with a simple migration.
- `Profile` is a separate model linked via `OneToOneField`, separating "auth-critical" data (username, password, permissions) from "enriched" data (bio, avatar, date of birth). This split came from the original class diagram.

---

## ADR-003: Pragmatic auth using `django.contrib.auth`

**Date:** 2026-04-23
**Status:** Accepted

### Context

Authentication scope includes registration, login, logout, and password reset. Django provides `django.contrib.auth` with battle-tested views and forms for all of these.

### Decision

Use `django.contrib.auth` views/forms as foundation; customize templates and add our own registration view (Django ships login/logout/password-reset but not a registration view by convention).

### Rationale

- Rolling our own auth is a classic mistake. Security edge cases (timing attacks, session fixation, password storage) are already handled by Django.
- Scope of the assignment does not require custom auth flows (e.g., 2FA, social login).
- Aligns with the team's originally recorded principle of "leverage built-in framework tools over building from scratch."

### Consequences

- Fast implementation of auth module.
- If social login or MFA becomes a requirement later, `django-allauth` plugs in cleanly.

---

## ADR-004: Workout data model — separate `Set` table, not JSON

**Date:** 2026-04-23
**Status:** Accepted (to be implemented in Phase 6+)

### Context

A workout consists of multiple exercises, each with multiple sets (reps × weight). There are two natural ways to model this:

1. **Nested:** `WorkoutExercise.sets` as a `JSONField` containing an array of `{reps, weight}` dicts.
2. **Relational:** a dedicated `Set` table with FK to `WorkoutExercise`.

### Decision

Relational. `Set` is a model.

### Rationale

- Progression queries (e.g., "max weight on bench press last month", "average reps per set in May") become trivial with a flat table and miserable with nested JSON.
- Per-set editing, ordering, and later features (RPE, rest time, failure flags) all extend cleanly.
- Storage cost difference is negligible for this scale.

### Consequences

- Slightly more tables and queries.
- Any analytics / charting feature in the future is drastically simpler.

---

## ADR-005: Routines are *copied* into Workouts, not referenced

**Date:** 2026-04-23
**Status:** Accepted (to be implemented in Phase 8+)

### Context

When a user starts a workout from a pre-defined routine, the system needs to link the session to the template. Two approaches:

1. **Reference:** `Workout` has a foreign key to `Routine` and resolves exercises dynamically.
2. **Copy:** on "start workout from routine", copy the routine's exercises into the workout as owned records.

### Decision

Copy.

### Rationale

- Users edit workouts mid-session — substitute exercises, skip sets, add extras. If workouts referenced a routine, any future edit to the routine would retroactively corrupt historical workouts.
- Templates and live sessions serve different purposes: templates are mutable plans, workouts are immutable history.

### Consequences

- Slight duplication of data.
- Historical integrity of logged workouts is guaranteed.
- Routine changes only affect future sessions started from that routine.

## ADR-006: Tailwind CSS v4 Standalone (no Node.js)

**Date:** 2026-04-24
**Status:** Accepted

### Context

Styling the frontend requires a CSS framework. Tailwind was the original team choice. The `django-tailwind` package offers three integration templates: Tailwind v4 Standalone (Go binary, no Node), Tailwind v4 Full (requires Node + npm), and Tailwind v3 Full (legacy).

### Decision

Tailwind v4 Standalone.

### Rationale

- Zero Node.js dependency at runtime — fewer moving parts and fewer ways for Windows setup to break between sessions.
- Node is still installed locally for future needs, but not required for Tailwind compilation.
- Plugin ecosystem (typography, forms) not expected to be needed for a gym-tracking MVP. If later required, migrating to the Full template is a mechanical switch.
- The solo-developer context rewards simplicity over flexibility.

### Consequences

- `python manage.py tailwind install` downloads a `tailwindcss-windows-x64.exe` inside the venv (excluded from Git).
- `python manage.py tailwind start` is the dev watcher. `tailwind build` compiles once (used before deploy or for static check).
- Compiled CSS at `theme/static/css/dist/styles.css` is a build artifact and excluded from version control.

---

## ADR-007: HTMX + Alpine.js via CDN, not npm

**Date:** 2026-04-24
**Status:** Accepted

### Context

The stack includes HTMX (for partial page updates driven by the server) and Alpine.js (for small client-side interactivity). Both can be installed via npm or loaded via CDN.

### Decision

CDN, loaded in `base.html`:
- HTMX: `https://unpkg.com/htmx.org@2.0.3`
- Alpine: `https://unpkg.com/alpinejs@3.14.1/dist/cdn.min.js`

### Rationale

- Both libraries are small (~10-15 KB each minified) and designed to work as drop-in `<script>` tags.
- Avoiding an npm build step keeps the project simpler, consistent with ADR-006 (Standalone Tailwind).
- Versions are pinned in the URLs, providing reproducible builds without a lockfile.

### Consequences

- First page load requires external CDN access. Acceptable in development; would need reconsideration for offline or air-gapped deployment.
- Updating HTMX/Alpine means editing `base.html`, not a package file. Acceptable given infrequent updates.

---

## ADR-008: Dedicated `pages` app for institutional pages

**Date:** 2026-04-24
**Status:** Accepted

### Context

The homepage, about page, and other institutional (non-domain-specific) views need a home. Options: put them in `config/`, reuse another app, or create a new one.

### Decision

New app `pages`.

### Rationale

- Keeps domain apps (`accounts`, `workouts`, etc.) focused on their bounded context.
- `config/` is for project-level configuration, not business logic.
- Low cost: a Django app is a folder with six tiny files.

### Consequences

- Any future static-content page (about, privacy, terms) has an obvious home.
- Homepage URL lives at `pages.urls` under namespace `pages`, accessed in templates as `{% url 'pages:home' %}`.