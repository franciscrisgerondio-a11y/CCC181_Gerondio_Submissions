from flask import Flask, abort, redirect, render_template, request, url_for

app = Flask(__name__)

SERVICES = [
    {"id": 1, "name": "Court 1"},
    {"id": 2, "name": "Court 2"},
    {"id": 3, "name": "Court 3"},
]

TICKETS = [
    {"id": 1, "number": 1, "name": "Ana", "email": "ana@school.edu",
     "service_id": 1, "players": 2, "status": "waiting"},
    {"id": 2, "number": 1, "name": "Ben", "email": "ben@school.edu",
     "service_id": 2, "players": 2, "status": "waiting"},
    {"id": 3, "number": 2, "name": "Carla", "email": "carla@school.edu",
     "service_id": 1, "players": 4, "status": "waiting"},
]


@app.route("/")
def index():
    return render_template("index.html", tickets=TICKETS, services=SERVICES)


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


@app.route("/join", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        service_id = request.form.get("service_id", type=int)
        if not name:
            return render_template("join.html", services=SERVICES,
                                   error="Please enter your name."), 400
        if service_id not in [s["id"] for s in SERVICES]:
            return render_template("join.html", services=SERVICES,
                                   error="Please choose a court."), 400

        new_id = max((t["id"] for t in TICKETS), default=0) + 1
        number = max((t["number"] for t in TICKETS if t["service_id"] == service_id),
                     default=0) + 1
        TICKETS.append({"id": new_id, "number": number, "name": name, "email": "",
                        "service_id": service_id, "players": 1, "status": "waiting"})
        return redirect(url_for("ticket", ticket_id=new_id))
    return render_template("join.html", services=SERVICES)


if __name__ == "__main__":
    app.run(debug=True)