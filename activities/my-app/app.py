from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "dev-only-change-me"  # Week 11 moves this into an environment variable

SERVICES = [
    {"id": 1, "name": "Court 1"},
    {"id": 2, "name": "Court 2"},
    {"id": 3, "name": "Court 3"},
]

# status is one of: waiting, called, served, no-show
TICKETS = [
    {"id": 12, "number": 12, "name": "Ana", "email": "ana@school.edu",
     "service_id": 1, "players": 2, "status": "called"},
    {"id": 13, "number": 13, "name": "Carla", "email": "carla@school.edu",
     "service_id": 1, "players": 4, "status": "waiting"},
    {"id": 14, "number": 14, "name": "Ben", "email": "ben@school.edu",
     "service_id": 2, "players": 2, "status": "waiting"},
]


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/join")
def join_form():
    return render_template("join.html", services=SERVICES)


@app.post("/join")
def join():
    name = request.form.get("name", "").strip()
    service_id = request.form.get("service_id", type=int)
    if not name:
        return render_template("join.html", services=SERVICES,
                               error="Please enter your name."), 400
    if service_id not in [s["id"] for s in SERVICES]:
        return render_template("join.html", services=SERVICES,
                               error="Please choose a court."), 400

    new_id = max((t["id"] for t in TICKETS), default=0) + 1
    TICKETS.append({"id": new_id, "number": new_id, "name": name, "email": "",
                    "service_id": service_id, "players": 1, "status": "waiting"})
    return redirect(url_for("ticket", ticket_id=new_id))


@app.route("/queue/<int:ticket_id>")
def ticket(ticket_id):
    t = next((t for t in TICKETS if t["id"] == ticket_id), None)
    if t is None:
        abort(404)
    ahead = [x for x in TICKETS
             if x["service_id"] == t["service_id"]
             and x["status"] == "waiting"
             and x["number"] < t["number"]]
    service = next(s for s in SERVICES if s["id"] == t["service_id"])
    return render_template("ticket.html", ticket=t, service=service, ahead=len(ahead))


@app.route("/staff")
def staff_dashboard():
    return "Staff dashboard coming soon"


if __name__ == "__main__":
    app.run(debug=True)