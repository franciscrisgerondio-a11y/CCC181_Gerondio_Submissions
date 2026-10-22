from datetime import datetime

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

app = Flask(__name__)
app.secret_key = "dev-only-change-me"  # Week 11 moves this into an environment variable

SERVICES = [
    {"id": 1, "name": "Court 1"},
    {"id": 2, "name": "Court 2"},
    {"id": 3, "name": "Court 3"},
]

# id is used in URLs, number is shown to players (continuous across courts).
# status is one of: waiting, called, served, no-show
TICKETS = [
    {"id": 12, "number": 12, "name": "Ana", "email": "ana@school.edu",
     "service_id": 1, "players": 2, "status": "called", "joined_at": "10:20 AM"},
    {"id": 13, "number": 13, "name": "Carla", "email": "carla@school.edu",
     "service_id": 1, "players": 4, "status": "waiting", "joined_at": "10:30 AM"},
    {"id": 14, "number": 14, "name": "Ben", "email": "ben@school.edu",
     "service_id": 2, "players": 2, "status": "waiting", "joined_at": "10:42 AM"},
]


def waiting_in(service_id):
    return [t for t in TICKETS
            if t["service_id"] == service_id and t["status"] == "waiting"]


def services_with_counts():
    return [{**s, "waiting": len(waiting_in(s["id"]))} for s in SERVICES]


def waiting_total():
    return sum(1 for t in TICKETS if t["status"] == "waiting")


@app.context_processor
def inject_nav():
    """Lets the navbar link to the visitor's own ticket after they join."""
    ticket_id = session.get("ticket_id")
    if not any(t["id"] == ticket_id for t in TICKETS):
        ticket_id = None
    return {"my_ticket_id": ticket_id}


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/join")
def join_form():
    return render_template("join.html", services=services_with_counts(),
                           waiting_total=waiting_total(), form={}, errors={})


@app.post("/join")
def join():
    form = request.form
    name = form.get("name", "").strip()
    service_id = form.get("service_id", type=int)
    players = form.get("players", type=int)

    errors = {}
    if not name:
        errors["name"] = "Enter your name."
    elif len(name) > 50:
        errors["name"] = "Use 50 characters or fewer."
    if service_id not in [s["id"] for s in SERVICES]:
        errors["service_id"] = "Choose a court."
    if players not in (2, 4):
        errors["players"] = "Choose 2 or 4 players."

    if errors:
        flash("Please fix the highlighted fields.", "danger")
        return render_template("join.html", services=services_with_counts(),
                               waiting_total=waiting_total(),
                               form=form, errors=errors), 400

    new_id = max((t["id"] for t in TICKETS), default=0) + 1
    TICKETS.append({"id": new_id, "number": new_id, "name": name, "email": "",
                    "service_id": service_id, "players": players,
                    "status": "waiting",
                    "joined_at": datetime.now().strftime("%I:%M %p").lstrip("0")})
    session["ticket_id"] = new_id
    flash(f"You joined the queue. Your ticket is #{new_id}.", "success")
    return redirect(url_for("ticket", ticket_id=new_id))


@app.route("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = next((t for t in TICKETS if t["id"] == ticket_id), None)
    if t is None:
        abort(404)
    ahead = [x for x in waiting_in(t["service_id"]) if x["number"] < t["number"]]
    service = next(s for s in SERVICES if s["id"] == t["service_id"])
    return render_template("ticket.html", ticket=t, service=service, ahead=len(ahead))


@app.route("/staff")
def staff_dashboard():
    return "Staff dashboard coming soon"


if __name__ == "__main__":
    app.run(debug=True)