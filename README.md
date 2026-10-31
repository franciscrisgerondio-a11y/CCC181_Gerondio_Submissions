# PivotPB

PivotPB is a queue system for pickleball open play on campus courts. Players join the line for a court and see their ticket, status and place in the line on their phone, while game organizers call, serve or mark groups as no show from a dashboard. It replaces the paddle stack, where the player whose paddle sits deepest in the pile plays next and nobody can see the real order. Built for CCC181 with Flask, Jinja and Bootstrap 5. Since Week 4 the queue is saved in PostgreSQL, so it survives a restart.

## What it does

* **Join** (`/join`): a player enters a name, picks an active court that shows how many groups are waiting, and chooses a group of 2 or 4. The server checks every field and keeps what was typed when something is wrong.
* **My place** (`/queue/<id>`): shows the ticket code, court, status, the time joined and how many groups are ahead. It refreshes every 5 seconds and shows a message box when the ticket is called.
* **Your tickets**: every page lists all of a player's active tickets, and an alert appears on any page when one of them is called.
* **Staff dashboard** (`/staff`): shows the waiting count for each court, one queue per court in order, a Call next button for each court, and Call, Serve, No show and Delete buttons on each row. It refreshes every 5 seconds.
* **Manage courts** (`/staff/services`): staff can add, rename and switch off a court. A court that is off no longer appears on the join form. A court that has tickets cannot be deleted.

Tickets use the code `C<court>-<number>`, for example `C2-001`. Each court has its own numbering, and a number is never reused.

The requirements for this app are in [docs/requirements.md](docs/requirements.md).

## Run it

You need Python 3.11 or newer and Docker.

```bash
cp .env.example .env            # Windows: copy .env.example .env
```

Open `.env` and set your own password in both `POSTGRES_PASSWORD` and `DATABASE_URL`. Then:

```bash
docker compose up -d            # start PostgreSQL, wait until "healthy" in: docker compose ps
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
flask --app app db upgrade      # create the tables from the migrations
flask --app app seed            # add the starting courts (safe to run twice)
flask --app app run --debug
```

Open http://127.0.0.1:5000. To try it on a phone, run `flask --app app run --debug --host 0.0.0.0` and visit your laptop's IP address on the same Wi‑Fi.

Use `docker compose down` to stop the database and keep the data. `docker compose down -v` also deletes the data.

## Things to know

* **The staff pages have no login yet.** Anyone who opens `/staff` or `/staff/services` can call, serve, delete tickets and change courts. Staff login comes in Week 11 (issue "Protect staff routes (Week 11)").
* **The secret key is a development value.** Week 11 moves it into an environment variable.
* **The database password is not in Git.** It lives in `.env`, which is ignored. `.env.example` shows the variables the app needs.
* **Each browser keeps its own tickets.** A browser gets a random token in its cookie, and a player can hold one active ticket per court. Only the browser that joined can leave that ticket.

## Project structure

```
app.py                  # routes, queue rules and validation
models.py               # SQLAlchemy models: Court, Visitor, Ticket
compose.yaml            # PostgreSQL 17 in Docker
.env.example            # variables the app needs (copy to .env)
requirements.txt        # packages to rebuild the environment
migrations/             # database migrations (committed)
templates/
    base.html           # shared layout, navigation and flash messages
    index.html          # home page
    join.html           # join form
    ticket.html         # My place
    staff.html          # staff dashboard page
    services.html       # Manage courts
    _my_tickets.html    # Your tickets strip and called alert (refreshed live)
    _staff_live.html    # staff counts and queues (refreshed live)
static/
    css/style.css       # PivotPB design
    js/main.js          # court dropdown, double submit guard, live refresh, delete confirm
docs/
    requirements.md     # living requirements list
    week3/              # personas, wireframes, self review, accessibility, usability test, report
    week4/              # schema, ERD, self review, validation, persistence, report
```

## Routes

| URL | Method | What it does |
| --- | --- | --- |
| `/` | GET | Home page |
| `/join` | GET, POST | Show the join form, create a ticket |
| `/queue/<id>` | GET | My place for one ticket |
| `/queue/<id>/status.json` | GET | Status and position, polled by My place |
| `/queue/<id>/leave` | POST | Leave the queue (owner only) |
| `/api/courts` | GET | Waiting count for each active court |
| `/partials/my-tickets` | GET | HTML for the Your tickets strip |
| `/staff` | GET | Staff dashboard |
| `/staff/live` | GET | HTML for the dashboard, polled every 5 seconds |
| `/staff/tickets/<id>/<action>` | POST | Call, serve or no show for one ticket |
| `/staff/tickets/<id>/delete` | POST | Delete a mistaken ticket |
| `/staff/courts/<id>/call-next` | POST | Call the next waiting group on a court |
| `/staff/services` | GET, POST | List courts, add a court |
| `/staff/services/<id>` | POST | Rename a court or switch it on or off |
| `/staff/services/<id>/delete` | POST | Delete a court that has no tickets |

## Documents

* Week 3: personas, wireframes, self review, accessibility results, the usability test and the report are in `docs/week3/`. The report is `docs/week3/report.md`.
* Week 4: the schema, ERD, self review, validation and persistence evidence are in `docs/week4/`. The report is `docs/week4/report.md`.