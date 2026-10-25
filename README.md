# PivotPB

PivotPB is a queue system for pickleball open play on campus courts. Players join the line for a court and see their ticket, status and place in the line on their phone, while game organizers call, serve or mark groups as no show from a dashboard. It replaces the paddle stack, where the player whose paddle sits deepest in the pile plays next and nobody can see the real order. Built for CCC181 Week 3 with Flask, Jinja and Bootstrap 5.

## What it does

* **Join** (`/join`): a player enters a name, picks a court that shows how many groups are waiting, and chooses a group of 2 or 4. The server checks every field and keeps what was typed when something is wrong.
* **My place** (`/queue/<id>`): shows the ticket code, court, status and how many groups are ahead. It refreshes every 5 seconds and shows a message box when the ticket is called.
* **Your tickets**: every page lists all of a player's active tickets, and an alert appears on any page when one of them is called.
* **Staff dashboard** (`/staff`): shows the waiting count for each court, one queue per court in order, a Call next button for each court, and Call, Serve and No show buttons on each row. It refreshes every 5 seconds.

Tickets use the code `C<court>-<number>`, for example `C2-001`. Each court has its own numbering, so several courts can each have a `001`.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
flask --app app run --debug
```

Open http://127.0.0.1:5000. To try it on a phone, run `flask --app app run --debug --host 0.0.0.0` and visit your laptop's IP address on the same Wi‑Fi.

## Things to know

* **The staff dashboard has no login yet.** Anyone who opens `/staff` can call, serve or remove tickets. Staff login comes in a later week.
* **Data lives in memory.** Tickets are kept in a Python list, so the queue starts empty and resets whenever the server restarts. Week 4 moves it into PostgreSQL.
* **The secret key is a development value.** Week 11 moves it into an environment variable.
* **Each browser keeps its own tickets.** A player can hold one active ticket per court, and only the browser that joined can leave that ticket.

## Project structure

```
app.py                  # routes, queue rules and validation
requirements.txt        # packages to rebuild the environment
templates/
    base.html           # shared layout, navigation and flash messages
    index.html          # home page
    join.html           # join form
    ticket.html         # My place
    staff.html          # staff dashboard page
    _my_tickets.html    # Your tickets strip and called alert (refreshed live)
    _staff_live.html    # staff counts and queues (refreshed live)
static/
    css/style.css       # PivotPB design
    js/main.js          # court dropdown, double submit guard, live refresh
docs/week3/             # personas, wireframes, self review, accessibility, usability test, report
```

## Routes

| URL | Method | What it does |
| --- | --- | --- |
| `/` | GET | Home page |
| `/join` | GET, POST | Show the join form, create a ticket |
| `/queue/<id>` | GET | My place for one ticket |
| `/queue/<id>/status.json` | GET | Status and position, polled by My place |
| `/queue/<id>/leave` | POST | Leave the queue (owner only) |
| `/api/courts` | GET | Waiting count for each court |
| `/partials/my-tickets` | GET | HTML for the Your tickets strip |
| `/staff` | GET | Staff dashboard |
| `/staff/live` | GET | HTML for the dashboard, polled every 5 seconds |
| `/staff/tickets/<id>/<action>` | POST | Call, serve or no show for one ticket |
| `/staff/courts/<id>/call-next` | POST | Call the next waiting group on a court |

## Week 3 documents

Personas, wireframes, self review, accessibility results, the usability test and the report are in `docs/week3/`. The report is `docs/week3/report.md`.