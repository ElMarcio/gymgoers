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


### Implementation note (2026-04-26)

 - When adding an exercise to a workout via the public UI (Phase 7, Block 3), the system will auto-create 3 empty sets by default (reps=0, weight_kg=0). Users typically perform 3-5 sets per exercise; pre-populating reduces clicks. The admin interface keeps the manual workflow because admin is for power users / debug.
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

---

## ADR-009: Auth module — pragmatic Django stack + known gotchas

**Date:** 2026-04-24
**Status:** Accepted

### Context

Implementing the authentication module (registration, login, logout, password reset) on top of the custom `User` model from ADR-002. Three specific technical decisions were made.

### Decisions

**1. Email backend: console in development**

`EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'` — password reset emails are printed to the `runserver` terminal instead of sent via SMTP. No external credentials or services needed in dev. Production would switch to an SMTP backend (e.g. SendGrid, AWS SES) via environment variable.

**2. Custom `UserCreationForm` required for signup**

Django's built-in `django.contrib.auth.forms.UserCreationForm` is hardcoded to `auth.User` and breaks when `AUTH_USER_MODEL` is customized. Subclassed it in `accounts/forms.py`

---

## ADR-010: Exercise catalogue — curated data via Django fixture

**Date:** 2026-04-26
**Status:** Accepted

### Context

The workout tracking module (Phase 7) requires users to select exercises when logging sets. Without a pre-populated catalogue, the app is unusable on first launch. Three approaches were considered:

1. **User-generated:** users create their own exercises ad-hoc when logging workouts.
2. **Data migration:** ship exercises as part of a Django migration.
3. **JSON fixture loaded via `loaddata`:** curated list, kept versioned alongside code.

### Decision

JSON fixture in `exercises/fixtures/exercises_seed.json`. 50 exercises covering the seven defined muscle groups (chest, back, legs, shoulders, arms, core, full body) with realistic equipment distribution.

### Rationale

- **User-generated rejected for MVP:** explodes the surface area (validation, deduplication, moderation, UI for creation, soft-delete on misuse). All deferrable.
- **Data migration rejected:** infrastructural seed (e.g. permission groups) belongs in migrations; domain data does not. Migrations are difficult to edit/extend; fixtures are JSON anyone can update.
- **Fixture pros:** versioned in Git, easily extended, idempotent via `loaddata`, well-known Django convention.

### Consequences

- Catalogue is curated and consistent.
- Adding new exercises is a one-line edit in the JSON + `python manage.py loaddata`.
- If "user-submitted exercises" becomes a future requirement, the model needs `created_by` (FK to User), `is_approved` flag, and admin moderation. Mechanical addition; nothing in current schema blocks it.

### Implementation note

The `Exercise.created_at` field originally used `auto_now_add=True`, which silently fails during `loaddata` (the auto-fill mechanism is bypassed by fixtures, leaving the column null and triggering a `NotNullViolation`). Changed to `default=timezone.now` for compatibility with both ORM and fixtures. This is a documented Django gotcha worth remembering for any seedable model.

---

## ADR-011: HTMX-driven dual-template views (full page vs fragment)

**Date:** 2026-04-26
**Status:** Accepted

### Context

The exercise catalogue supports live search and filtering. Two implementation approaches:

1. **Full page reload on every keystroke/filter change:** simple, but UX is poor (loses scroll position, flickers, slow).
2. **Client-side JavaScript framework:** React/Vue + JSON API. Requires API layer, frontend build, state management.
3. **HTMX:** server returns HTML fragments on demand; HTMX swaps them into the DOM.

### Decision

HTMX. The `ExerciseListView` overrides `get_template_names()` to return `_exercise_list_fragment.html` for requests with the `HX-Request` header, and the full `exercise_list.html` otherwise. Same URL, same view, two output modes.

### Rationale

- **Stays consistent with the project's HTMX-first stance** (declared at project inception, before solo run).
- **No API surface needed.** The fragment template is just the part of the page that changes; the wrapper template includes it on full page loads.
- **`hx-push-url="true"`** keeps the URL in sync with filter state — refresh-friendly, shareable links, browser back/forward works.
- **Underscore prefix** on the fragment template (`_exercise_list_fragment.html`) is convention to flag it as a partial that should not be rendered standalone.

### Consequences

- Pesquisa-as-you-type with 300ms debounce feels instant without any client-side state.
- Trade-off: any view that needs HTMX-driven updates must also implement the dual-template pattern. Acceptable boilerplate.
- If we ever build a mobile app (ADR-001 leaves it as "vague possibility"), these views need wrapping with DRF — non-trivial but not blocked by this decision.

---

## ADR-012: Workout state machine — in_progress → finished

**Date:** 2026-04-26
**Status:** Accepted

### Context

Workouts have two distinct phases: while being logged (mutable, lots of edits) and after the user is done (immutable historical record). The system needs to enforce this invariant: finished workouts cannot be modified, even by their owner.

### Decision

`Workout.status` field with two values: `in_progress` and `finished`. Transition is one-way: in_progress → finished. There is no "reopen finished workout" flow.

Every mutation view (set update, set create, set delete, add exercise, update meta) checks `workout.is_in_progress` and returns 403 if not. UI templates conditionally render edit affordances only when `is_in_progress`.

`Workout.finish()` runs cleanup before transitioning: deletes sets with `reps=0` and orphaned WorkoutExercises (those with no remaining sets). Raises `ValueError` if cleanup leaves the workout with zero meaningful sets — preventing empty workouts from being marked as finished.

### Rationale

- **One-way transition** keeps the model simple. Reopening a workout to edit retroactively undermines the integrity of the history. Out of scope for MVP.
- **Cleanup on finish** prevents pollution of the history with placeholder data (empty sets pre-created when adding an exercise; see ADR-004 implementation note).
- **Validation that something was actually logged** prevents edge cases where the user clicks "Finish" on a fresh workout by mistake.
- **Defense at multiple layers**: model method validates, view catches the exception and surfaces via flash messages, template hides edit affordances on finished workouts.

### Consequences

- Users cannot edit history. If they realize a workout was logged with wrong data, the workaround is "delete and re-create" (which is destructive). Acceptable for MVP.
- The "no reopen" rule may be relaxed in future versions if user feedback demands it.

---

## ADR-013: HTMX inline-edit pattern with server-rendered fragments

**Date:** 2026-04-26
**Status:** Accepted

### Context

The workout-in-progress page is heavily interactive: each set has 4 editable fields (reps, weight, is_warmup, completed), users add and remove sets, edit workout title and notes, all without leaving the page.

Two viable approaches:

1. **Client-side state (JS framework):** load the workout once, manage state in React/Alpine, sync to backend via JSON API.
2. **HTMX with server-rendered fragments:** every interaction is a small HTTP request that returns a HTML snippet replacing part of the DOM.

### Decision

Approach 2 (HTMX). Each interactive component (set row, workout exercise block, workout meta) has a corresponding fragment template (`_set_row.html`, `_workout_exercise_block.html`, `_workout_meta.html`) and a small view that returns it.

### Rationale

- **No JSON API surface needed.** Same Django views, just rendering smaller templates conditionally. Reuses existing form validation (ModelForm).
- **Lower complexity** than maintaining client state synchronized with server state.
- **Progressive enhancement preserved:** if HTMX fails to load, regular form submissions would still work (with full page reloads). Forms have proper `<form>` semantics.
- **Validation is server-side only** — ModelForm rules apply on every save, no duplication.

### Consequences

- Many small endpoints (one per editable component). Discoverable in `urls.py`.
- Fragment templates with leading underscore (`_set_row.html`) signal partial-only by convention.
- View dispatch checks `request.headers.get('HX-Request')` only when the URL serves both full page and fragment (the exercise list view in Phase 6 does this; workout fragments are dedicated endpoints, no detection needed).
- Trade-off: each interaction is a round-trip. Not a problem on local dev or low-latency hosting; could feel sluggish on slow connections. Future optimization: optimistic UI with `hx-swap="outerHTML transition:true"` plus rollback on error.