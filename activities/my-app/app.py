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

STATUS_LABELS = {"waiting": "Waiting", "called": "Called", "served": "Served",
                 "no-show": "No show", "left": "Left"}

# id is unique forever and is used in URLs.
# number counts within one court, so every court has its own 001, 002, ...
# The ticket code shown to people is C<court id>-<number>, for example C1-011.
# status is one of: waiting, called, served, no-show, left
TICKETS = [
    {"id": 1, "number": 11, "name": "Ana", "email": "ana@school.edu",
     "service_id": 1, "players": 2, "status": "called", "joined_at": "10:20 AM"},
    {"id": 2, "number": 12, "name": "Carla", "email": "carla@school.edu",
     "service_id": 1, "players": 4, "status": "waiting", "joined_at": "10:30 AM"},
    {"id": 3, "number": 1, "name": "Ben", "email": "ben@school.edu",
     "service_id": 2, "players": 2, "status": "waiting", "joined_at": "10:42 AM"},
]

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
        subline = f"Head to {court} now."
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
            "can_leave": status in ("waiting", "called")}


def back_to_dashboard():
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("filter", type=int)))


@app.context_processor
def inject_nav():
    """Lets the navbar link to the visitor's own ticket after they join."""
    ticket_id = session.get("ticket_id")
    if find_ticket(ticket_id) is None:
        ticket_id = None
    return {"my_ticket_id": ticket_id}


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
    session["ticket_id"] = new_id
    flash(f"You joined the queue. Your ticket is {ticket_code(new_ticket)}.", "success")
    return redirect(url_for("ticket", ticket_id=new_id))


@app.get("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = find_ticket(ticket_id)
    if t is None:
        abort(404)
    return render_template("ticket.html", ticket=t,
                           service=find_service(t["service_id"]),
                           view=describe(t))


@app.post("/queue/<int:ticket_id>/leave")
def leave(ticket_id):
    t = find_ticket(ticket_id)
    if t is None:
        abort(404)
    if t["status"] not in ("waiting", "called"):
        return redirect(url_for("ticket", ticket_id=ticket_id))
    t["status"] = "left"
    if session.get("ticket_id") == ticket_id:
        session.pop("ticket_id")
    flash("You left the queue.", "info")
    return redirect(url_for("index"))


# ---------- staff routes (login comes in a later week) ----------

@app.get("/staff")
def staff_dashboard():
    selected = request.args.get("service_id", type=int)
    if selected not in [s["id"] for s in SERVICES]:
        selected = None

    all_courts = []
    for s in SERVICES:
        queue = sorted((t for t in TICKETS
                        if t["service_id"] == s["id"]
                        and t["status"] in ("waiting", "called")),
                       key=lambda t: t["number"])
        all_courts.append({"service": s, "tickets": queue,
                           "waiting": sum(1 for t in queue if t["status"] == "waiting")})
    shown = [c for c in all_courts if selected in (None, c["service"]["id"])]
    return render_template("staff.html", all_courts=all_courts, shown=shown,
                           services=SERVICES, selected=selected)


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