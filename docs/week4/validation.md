# Validation in three layers

The same rules are checked in the browser, in Flask and in PostgreSQL. The browser helps honest users. Flask is the real gatekeeper. The database is the last line of defense, because it still holds when a bug or a hand typed request skips the first two.

## Browser

The join form uses `required` on the name and on the 2 or 4 players choice, and `maxlength="50"` on the name so it matches `varchar(50)`. The court picker is a hidden field, so the browser cannot check it. Flask and the foreign key check it instead.

## Flask (curl, skipping the form)

Before the tests, `SELECT count(*) FROM tickets;` gave 2. After all four requests it was still 2, so nothing bad was saved.

| Rule | Layer | How I tested it | What happened |
| --- | --- | --- | --- |
| Name, court and players are required | Flask | `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=" -d "service_id=999" -d "players=3"` | `HTTP/1.1 400 BAD REQUEST`, form shows "Enter your name.", "Choose a court." and "Choose 2 or 4 players." |
| Group size must be 2 or 4 | Flask | `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=Test" -d "service_id=1" -d "players=3"` | 400, "Choose 2 or 4 players." |
| Name is at most 50 characters | Flask | `$long = "x" * 200` then `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=$long" -d "service_id=1" -d "players=2"` | 400, "Use 50 characters or fewer." |
| A switched off court cannot be joined | Flask | Court 3 switched off in Manage courts, then `curl.exe -i -X POST http://127.0.0.1:5000/join -d "name=Test" -d "service_id=3" -d "players=2"` | 400, "Choose a court." and Court 3 is missing from the dropdown |

## Database (psql, skipping Flask)

| Rule | Constraint type | How I tested it | What happened |
| --- | --- | --- | --- |
| A ticket needs a court that exists | FOREIGN KEY | `INSERT INTO tickets (...) VALUES (999, 1, 50, 'Test', 2);` | `ERROR: insert or update on table "tickets" violates foreign key constraint "tickets_court_id_fkey"` and `DETAIL: Key (court_id)=(999) is not present in table "courts".` |
| Only the five statuses are allowed | CHECK | `UPDATE tickets SET status = 'lost' WHERE id = 1;` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_status"` |
| Group size must be 2 or 4 | CHECK | `INSERT ... players 3` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_players"` |
| A group name cannot be blank | CHECK | `INSERT ... group_name '   '` | `ERROR: new row for relation "tickets" violates check constraint "ck_tickets_group_name_not_blank"` |
| A ticket needs a group size | NOT NULL | `INSERT` without `players` | `ERROR: null value in column "players" of relation "tickets" violates not-null constraint` |
| Two courts cannot share a name | UNIQUE | `INSERT INTO courts (name) VALUES ('Court 2');` | `ERROR: duplicate key value violates unique constraint "courts_name_key"` and `DETAIL: Key (name)=(Court 2) already exists.` |
| A ticket number is used once per court | UNIQUE | `INSERT ... court_id 1, number 1` | `ERROR: duplicate key value violates unique constraint "uq_tickets_court_number"` and `DETAIL: Key (court_id, number)=(1, 1) already exists.` |
| One active ticket per browser per court | UNIQUE (partial index) | second active `INSERT` for visitor 2 on court 1 | `ERROR: duplicate key value violates unique constraint "uq_tickets_one_active_per_court"` and `DETAIL: Key (visitor_id, court_id)=(2, 1) already exists.` |
| A court with tickets cannot be deleted | ON DELETE RESTRICT | `DELETE FROM courts WHERE id = 1;` | `ERROR: update or delete on table "courts" violates foreign key constraint "tickets_court_id_fkey" on table "tickets"` and `DETAIL: Key (id)=(1) is still referenced from table "tickets".` |

A good row, to show the defaults the database fills in: `INSERT INTO tickets (court_id, visitor_id, number, group_name, players) VALUES (1, 1, 51, 'Good', 2) RETURNING id, status, created_at;` succeeded with status `waiting` and a `created_at` time that the database set. I deleted it afterward.

## No SQL in f-strings

`git grep -n -E "f.(SELECT|INSERT|UPDATE|DELETE) " -- "*.py"` printed nothing. A second check for `execute(` found two lines, and neither is hand written SQL. `app.py:74` runs `db.session.execute(stmt)` on a query built with `db.select`, and `migrations/env.py:62` is a comment inside Alembic's generated file. Every query goes through SQLAlchemy, which sends values separately from the SQL.

## Most useful error

`ck_tickets_group_name_not_blank` showed me that NOT NULL does not stop an empty or space only name, which is why I added the CHECK during my schema review.