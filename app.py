import os
import uuid
from datetime import timedelta, timezone

from dotenv import load_dotenv
from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_migrate import Migrate
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import Court, Ticket, Visitor, db

load_dotenv()

app = Flask(__name__)
app.secret_key = "dev-only-change-me"  # Week 11 moves this into an environment variable
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
app.config["SQLALCHEMY_ECHO"] = os.environ.get("SQLALCHEMY_ECHO") == "1"

db.init_app(app)
migrate = Migrate(app, db)

STATUS_LABELS = {"waiting": "Waiting", "called": "Called", "served": "Served",
                 "no-show": "No show", "left": "Left"}
ACTIVE = ("waiting", "called")

# action -> (statuses it is allowed from, new status)
ACTIONS = {
    "call": ({"waiting"}, "called"),
    "serve": ({"called"}, "served"),
    "no-show": ({"waiting", "called"}, "no-show"),
}

PH_TIME = timezone(timedelta(hours=8))  # Philippine time has no daylight saving


# ---------- helpers ----------

def ticket_code(t):
    return f"C{t.court_id}-{t.number:03d}"


@app.template_filter("ticket_code")
def ticket_code_filter(t):
    return ticket_code(t)


@app.template_filter("status_label")
def status_label(status):
    return STATUS_LABELS.get(status, status)


@app.template_filter("local")
def local_time(value):
    """Show a database time in Philippine time, e.g. Oct 26, 08:01 AM."""
    return value.astimezone(PH_TIME).strftime("%b %d, %I:%M %p") if value else ""


def all_courts():
    return db.session.scalars(db.select(Court).order_by(Court.id)).all()


def courts_with_counts():
    """Each court with how many groups are waiting, counted by the database."""
    stmt = (db.select(Ticket.court_id, func.count())
            .where(Ticket.status == "waiting")
            .group_by(Ticket.court_id))
    counts = dict(db.session.execute(stmt).all())
    return [{"id": c.id, "name": c.name, "waiting": counts.get(c.id, 0)}
            for c in all_courts()]


def waiting_total():
    stmt = db.select(func.count()).select_from(Ticket).where(Ticket.status == "waiting")
    return db.session.scalar(stmt)


def people_ahead(t):
    """Count groups still waiting on the same court that joined before t.
    The position is computed, never stored."""
    stmt = (db.select(func.count()).select_from(Ticket)
            .where(Ticket.court_id == t.court_id,
                   Ticket.status == "waiting",
                   Ticket.number < t.number))
    return db.session.scalar(stmt)


def current_visitor():
    """The visitor for this browser, found through the token in its cookie."""
    try:
        token = uuid.UUID(session.get("visitor_token", ""))
    except (ValueError, TypeError, AttributeError):
        return None
    return db.session.scalar(db.select(Visitor).filter_by(token=token))


def my_tickets():
    """Every ticket this browser has created, oldest first."""
    visitor = current_visitor()
    if visitor is None:
        return []
    stmt = (db.select(Ticket).where(Ticket.visitor_id == visitor.id)
            .order_by(Ticket.created_at, Ticket.id))
    return db.session.scalars(stmt).all()


def card(t):
    return {"id": t.id, "code": ticket_code(t), "court": t.court.name,
            "status": t.status, "label": STATUS_LABELS[t.status],
            "url": url_for("ticket", ticket_id=t.id)}


def describe(t):
    """The words My place shows for a ticket in each status."""
    court = t.court.name
    ahead = people_ahead(t) if t.status == "waiting" else 0
    status = t.status
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
    courts = all_courts()
    selected = request.args.get("service_id", type=int)
    if selected not in [c.id for c in courts]:
        selected = None

    # One query for every active ticket, in the order groups joined.
    stmt = (db.select(Ticket).where(Ticket.status.in_(ACTIVE))
            .order_by(Ticket.court_id, Ticket.number))
    active = db.session.scalars(stmt).all()

    all_data = []
    for c in courts:
        queue = [t for t in active if t.court_id == c.id]
        all_data.append({"service": c, "tickets": queue,
                         "waiting": sum(1 for t in queue if t.status == "waiting")})
    shown = [c for c in all_data if selected in (None, c["service"].id)]
    return {"all_courts": all_data, "shown": shown, "selected": selected}


def back_to_dashboard():
    return redirect(url_for("staff_dashboard",
                            service_id=request.form.get("filter", type=int)))


@app.context_processor
def inject_nav():
    mine = my_tickets()
    active = [t for t in mine if t.status in ACTIVE]

    current = None
    if request.endpoint == "ticket":
        current = (request.view_args or {}).get("ticket_id")
    elif request.endpoint == "my_tickets_partial":
        current = request.args.get("current", type=int)

    # My place opens the ticket that needs attention most: called, else newest active.
    target = (next((t for t in active if t.status == "called"), None)
              or (active[-1] if active else None)
              or (mine[-1] if mine else None))

    return {"my_active": [card(t) for t in active],
            "current_ticket_id": current,
            "my_place_id": target.id if target else None,
            "has_tickets": bool(mine)}


# ---------- player routes ----------

@app.route("/")
def index():
    return render_template("index.html")


@app.get("/join")
def join_form():
    return render_template("join.html", services=courts_with_counts(),
                           waiting_total=waiting_total(), form={}, errors={})


@app.post("/join")
def join():
    form = request.form
    name = form.get("name", "").strip()
    service_id = form.get("service_id", type=int)
    players = form.get("players", type=int)
    court = db.session.get(Court, service_id) if service_id else None

    errors = {}
    if not name:
        errors["name"] = "Enter your name."
    elif len(name) > 50:
        errors["name"] = "Use 50 characters or fewer."
    if court is None:
        errors["service_id"] = "Choose a court."
    if players not in (2, 4):
        errors["players"] = "Choose 2 or 4 players."

    if errors:
        flash("Please fix the highlighted fields.", "danger")
        return render_template("join.html", services=courts_with_counts(),
                               waiting_total=waiting_total(),
                               form=form, errors=errors), 400

    # Find this browser's visitor row, or create it and remember its token.
    visitor = current_visitor()
    if visitor is None:
        visitor = Visitor()
        db.session.add(visitor)
        db.session.commit()
        session["visitor_token"] = str(visitor.token)

    for _ in range(3):
        # One active ticket per court for each browser. This also stops double taps.
        existing = db.session.scalar(
            db.select(Ticket).where(Ticket.visitor_id == visitor.id,
                                    Ticket.court_id == court.id,
                                    Ticket.status.in_(ACTIVE)))
        if existing:
            flash(f"You already have {ticket_code(existing)} on {court.name}. "
                  f"Here is your place.", "warning")
            return redirect(url_for("ticket", ticket_id=existing.id))

        # Numbers count up inside one court and are never reused.
        last = db.session.scalar(
            db.select(func.max(Ticket.number)).where(Ticket.court_id == court.id))
        ticket = Ticket(court=court, visitor=visitor, number=(last or 0) + 1,
                        group_name=name, players=players)
        db.session.add(ticket)
        try:
            db.session.commit()
        except IntegrityError:
            # Another request took this number, or a double tap made a second ticket.
            # The session must be rolled back before it can be used again.
            db.session.rollback()
            continue

        flash(f"You joined the queue. Your ticket is {ticket_code(ticket)}.", "success")
        return redirect(url_for("ticket", ticket_id=ticket.id))

    flash("Something went wrong saving your ticket. Please try again.", "danger")
    return render_template("join.html", services=courts_with_counts(),
                           waiting_total=waiting_total(), form=form, errors={}), 409


@app.get("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = db.get_or_404(Ticket, ticket_id)
    visitor = current_visitor()
    return render_template("ticket.html", ticket=t, service=t.court,
                           view=describe(t),
                           is_owner=visitor is not None and t.visitor_id == visitor.id)


@app.get("/queue/<int:ticket_id>/status.json")
def ticket_status(ticket_id):
    """Small JSON route that My place polls. Week 6 turns this into a REST API."""
    t = db.get_or_404(Ticket, ticket_id)
    return describe(t)


@app.get("/api/courts")
def courts_json():
    return {"courts": courts_with_counts(), "waiting_total": waiting_total()}


@app.get("/partials/my-tickets")
def my_tickets_partial():
    return render_template("_my_tickets.html")


@app.post("/queue/<int:ticket_id>/leave")
def leave(ticket_id):
    t = db.get_or_404(Ticket, ticket_id)
    visitor = current_visitor()
    if visitor is None or t.visitor_id != visitor.id:
        abort(403)
    if t.status not in ACTIVE:
        return redirect(url_for("ticket", ticket_id=ticket_id))
    t.status = "left"  # soft delete: the row stays for reports (FR-13)
    t.closed_at = func.now()
    db.session.commit()
    flash(f"You left the queue. {ticket_code(t)} is released.", "info")

    others = [x for x in my_tickets() if x.status in ACTIVE]
    if others:
        return redirect(url_for("ticket", ticket_id=others[-1].id))
    return redirect(url_for("index"))


# ---------- staff routes (login comes in a later week) ----------

@app.get("/staff")
def staff_dashboard():
    return render_template("staff.html", services=all_courts(), **staff_data())


@app.get("/staff/live")
def staff_live():
    return render_template("_staff_live.html", **staff_data())


@app.post("/staff/tickets/<int:ticket_id>/delete")
def delete_ticket(ticket_id):
    t = db.get_or_404(Ticket, ticket_id)
    code = ticket_code(t)
    db.session.delete(t)  # hard delete: the row is gone for good
    db.session.commit()
    flash(f"Ticket {code} was deleted.", "warning")
    return back_to_dashboard()


@app.post("/staff/tickets/<int:ticket_id>/<action>")
def staff_action(ticket_id, action):
    if action not in ACTIONS:
        abort(404)
    t = db.get_or_404(Ticket, ticket_id)
    allowed_from, new_status = ACTIONS[action]
    if t.status not in allowed_from:
        flash(f"{ticket_code(t)} is {STATUS_LABELS[t.status].lower()}, "
              f"so that action is not available.", "warning")
        return back_to_dashboard()
    t.status = new_status
    if new_status == "called":
        t.called_at = func.now()  # the database fills in the time
    else:
        t.closed_at = func.now()
    db.session.commit()
    flash(f"{ticket_code(t)} ({t.group_name}) marked {STATUS_LABELS[new_status].lower()}.", "info")
    return back_to_dashboard()


@app.post("/staff/courts/<int:service_id>/call-next")
def staff_call_next(service_id):
    court = db.get_or_404(Court, service_id)
    stmt = (db.select(Ticket)
            .where(Ticket.court_id == court.id, Ticket.status == "waiting")
            .order_by(Ticket.number).limit(1))
    t = db.session.scalar(stmt)
    if t is None:
        flash(f"No one is waiting on {court.name}.", "warning")
    else:
        t.status = "called"
        t.called_at = func.now()
        db.session.commit()
        flash(f"Called {ticket_code(t)} ({t.group_name}) on {court.name}.", "success")
    return back_to_dashboard()


@app.cli.command("seed")
def seed():
    """Add the starting courts if they are not there yet."""
    for name in ["Court 1", "Court 2", "Court 3"]:
        exists = db.session.scalar(db.select(Court).filter_by(name=name))
        if exists is None:
            db.session.add(Court(name=name))
    db.session.commit()
    print("Courts are ready.")


if __name__ == "__main__":
    app.run(debug=True)