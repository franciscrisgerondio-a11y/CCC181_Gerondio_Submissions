import secrets
from datetime import datetime

import os

from dotenv import load_dotenv
from flask_migrate import Migrate

from models import db
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)

app = Flask(__name__)
app.secret_key = "dev-only-change-me"  # Week 11 moves this into an environment variable

load_dotenv()
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_ECHO"] = os.environ.get("SQLALCHEMY_ECHO") == "1"

db.init_app(app)
migrate = Migrate(app, db)

# Changes every time the server starts, so old browser cookies cannot point
# at someone else's new ticket. Week 4 replaces this with a real database.
BOOT_ID = secrets.token_hex(4)

SERVICES = [
    {"id": 1, "name": "Court 1"},
    {"id": 2, "name": "Court 2"},
    {"id": 3, "name": "Court 3"},
]

STATUS_LABELS = {"waiting": "Waiting", "called": "Called", "served": "Served",
                 "no-show": "No show", "left": "Left"}
ACTIVE = ("waiting", "called")

# id is unique forever and is used in URLs.
# number counts within one court, so every court has its own 001, 002, ...
# The ticket code shown to people is C<court id>-<number>, for example C1-011.
# status is one of: waiting, called, served, no-show, left
TICKETS = []

# action -> (statuses it is allowed from, new status)
ACTIONS = {
    "call": ({"waiting"}, "called"),
    "serve": ({"called"}, "served"),
    "no-show": ({"waiting", "called"}, "no-show"),
}


# ---------- helpers ----------

def ticket_code(t):
    return f"C{t['service_id']}-{t['number']:03d}"


@app.template_filter("ticket_code")
def ticket_code_filter(t):
    return ticket_code(t)


@app.template_filter("status_label")
def status_label(status):
    return STATUS_LABELS.get(status, status)


def find_ticket(ticket_id):
    return next((t for t in TICKETS if t["id"] == ticket_id), None)


def find_service(service_id):
    return next(s for s in SERVICES if s["id"] == service_id)


def waiting_in(service_id):
    return sorted((t for t in TICKETS
                   if t["service_id"] == service_id and t["status"] == "waiting"),
                  key=lambda t: t["number"])


def services_with_counts():
    return [{**s, "waiting": len(waiting_in(s["id"]))} for s in SERVICES]


def waiting_total():
    return sum(1 for t in TICKETS if t["status"] == "waiting")


def my_tickets():
    """Every ticket this browser has created, oldest first."""
    found = (find_ticket(i) for i in session.get("my_tickets", []))
    return [t for t in found if t]


def card(t):
    return {"id": t["id"], "code": ticket_code(t),
            "court": find_service(t["service_id"])["name"],
            "status": t["status"], "label": STATUS_LABELS[t["status"]],
            "url": url_for("ticket", ticket_id=t["id"])}


def describe(t):
    """The words My place shows for a ticket in each status."""
    court = find_service(t["service_id"])["name"]
    ahead = sum(1 for x in waiting_in(t["service_id"]) if x["number"] < t["number"])
    status = t["status"]
    banner = ""

    if status == "waiting":
        headline = "You're in."
        subline = f"Stay nearby. We'll clearly let you know when {court} is ready."
        if ahead == 0:
            position = "You're next!"
        else:
            position = f"{ahead} {'group' if ahead == 1 else 'groups'} ahead of you"
    elif status == "called":
        headline = "You're up."
        subline = f"{court} is now available."
        position = "It's your turn"
        banner = f"Go to {court} now"
    elif status == "served":
        headline = "Game on."
        subline = "Your turn has started. Thanks for waiting."
        position = "Enjoy your game"
    elif status == "no-show":
        headline = "Missed your turn."
        subline = "You weren't at the court when called. Join again to get back in line."
        position = "Marked as no show"
    else:  # left
        headline = "See you next time."
        subline = "Join again whenever you're ready."
        position = "You left the queue"

    return {"status": status, "status_label": STATUS_LABELS[status],
            "ahead": ahead, "position": position, "headline": headline,
            "subline": subline, "banner": banner,
            "can_leave": status in ACTIVE}


def staff_data():
    selected = request.args.get("service_id", type=int)
    if selected not in [s["id"] for s in SERVICES]:
        selected = None

    all_courts = []
    for s in SERVICES:
        queue = sorted((t for t in TICKETS
                        if t["service_id"] == s["id"] and t["status"] in ACTIVE),
                       key=lambda t: t["number"])
        all_courts.append({"service": s, "tickets": queue,
                           "waiting": sum(1 for t in queue if t["status"] == "waiting")})
    shown = [c for c in all_courts if selected in (None, c["service"]["id"])]
    return {"all_courts": all_courts, "shown": shown, "selected": selected}


def back_to_dashboard():
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("filter", type=int)))


@app.before_request
def reset_stale_session():
    if session.get("boot") != BOOT_ID:
        session.clear()
        session["boot"] = BOOT_ID


@app.context_processor
def inject_nav():
    mine = my_tickets()
    active = [t for t in mine if t["status"] in ACTIVE]

    current = None
    if request.endpoint == "ticket":
        current = (request.view_args or {}).get("ticket_id")
    elif request.endpoint == "my_tickets_partial":
        current = request.args.get("current", type=int)

    # My place opens the ticket that needs attention most: called, else newest active.
    target = (next((t for t in active if t["status"] == "called"), None)
              or (active[-1] if active else None)
              or (mine[-1] if mine else None))

    return {"my_active": [card(t) for t in active],
            "current_ticket_id": current,
            "my_place_id": target["id"] if target else None,
            "has_tickets": bool(mine)}


# ---------- player routes ----------

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

    # One active ticket per court for each browser. This also stops double taps.
    existing = next((t for t in my_tickets()
                     if t["service_id"] == service_id and t["status"] in ACTIVE), None)
    if existing:
        flash(f"You already have {ticket_code(existing)} on "
              f"{find_service(service_id)['name']}. Here is your place.", "warning")
        return redirect(url_for("ticket", ticket_id=existing["id"]))

    # The id never repeats, so every ticket link stays unique.
    new_id = max((t["id"] for t in TICKETS), default=0) + 1
    # The number continues inside this court only. People who left no longer
    # count, so their number is reused only if they were last in that court.
    number = max((t["number"] for t in TICKETS
                  if t["service_id"] == service_id and t["status"] != "left"),
                 default=0) + 1

    new_ticket = {"id": new_id, "number": number, "name": name, "email": "",
                  "service_id": service_id, "players": players,
                  "status": "waiting",
                  "joined_at": datetime.now().strftime("%I:%M %p").lstrip("0")}
    TICKETS.append(new_ticket)
    session["my_tickets"] = (session.get("my_tickets", []) + [new_id])[-20:]
    flash(f"You joined the queue. Your ticket is {ticket_code(new_ticket)}.", "success")
    return redirect(url_for("ticket", ticket_id=new_id))


@app.get("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = find_ticket(ticket_id)
    if t is None:
        abort(404)
    return render_template("ticket.html", ticket=t,
                           service=find_service(t["service_id"]),
                           view=describe(t),
                           is_owner=ticket_id in session.get("my_tickets", []))


@app.get("/queue/<int:ticket_id>/status.json")
def ticket_status(ticket_id):
    """Small JSON route that My place polls. Week 6 turns this into a REST API."""
    t = find_ticket(ticket_id)
    if t is None:
        abort(404)
    return describe(t)


@app.get("/api/courts")
def courts_json():
    return {"courts": services_with_counts(), "waiting_total": waiting_total()}


@app.get("/partials/my-tickets")
def my_tickets_partial():
    return render_template("_my_tickets.html")


@app.post("/queue/<int:ticket_id>/leave")
def leave(ticket_id):
    t = find_ticket(ticket_id)
    if t is None:
        abort(404)
    if ticket_id not in session.get("my_tickets", []):
        abort(403)
    if t["status"] not in ACTIVE:
        return redirect(url_for("ticket", ticket_id=ticket_id))
    t["status"] = "left"
    flash(f"You left the queue. {ticket_code(t)} is released.", "info")

    others = [x for x in my_tickets() if x["status"] in ACTIVE]
    if others:
        return redirect(url_for("ticket", ticket_id=others[-1]["id"]))
    return redirect(url_for("index"))


# ---------- staff routes (login comes in a later week) ----------

@app.get("/staff")
def staff_dashboard():
    return render_template("staff.html", services=SERVICES, **staff_data())


@app.get("/staff/live")
def staff_live():
    return render_template("_staff_live.html", **staff_data())


@app.post("/staff/tickets/<int:ticket_id>/<action>")
def staff_action(ticket_id, action):
    t = find_ticket(ticket_id)
    if t is None or action not in ACTIONS:
        abort(404)
    allowed_from, new_status = ACTIONS[action]
    if t["status"] not in allowed_from:
        flash(f"{ticket_code(t)} is {STATUS_LABELS[t['status']].lower()}, "
              f"so that action is not available.", "warning")
        return back_to_dashboard()
    t["status"] = new_status
    flash(f"{ticket_code(t)} ({t['name']}) marked {STATUS_LABELS[new_status].lower()}.", "info")
    return back_to_dashboard()


@app.post("/staff/courts/<int:service_id>/call-next")
def staff_call_next(service_id):
    if service_id not in [s["id"] for s in SERVICES]:
        abort(404)
    queue = waiting_in(service_id)
    court = find_service(service_id)["name"]
    if not queue:
        flash(f"No one is waiting on {court}.", "warning")
    else:
        queue[0]["status"] = "called"
        flash(f"Called {ticket_code(queue[0])} ({queue[0]['name']}) on {court}.", "success")
    return back_to_dashboard()


if __name__ == "__main__":
    app.run(debug=True)