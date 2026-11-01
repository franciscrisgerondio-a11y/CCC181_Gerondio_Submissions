# Schema self-review

I reviewed the ERD in `schema.md` after leaving it for a while, using the six questions from Part 3.

**Works well:** Two unique rules do the heavy lifting for the queue. `UNIQUE (court_id, number)` means two groups can never share a ticket number on a court, and the partial unique index on `(visitor_id, court_id)` for active tickets means a double tap cannot create a second ticket. Both meet NFR-02 and FR-09 inside the database, so they hold even if a Flask check is skipped. (Question 4, bad data.)

**Problem:** `group_name` and `courts.name` are NOT NULL, but PostgreSQL treats an empty string or a string of spaces as a real value. A request that skips the form could save a ticket with a blank name. (Question 4, bad data.)
**Change:** I added `CHECK (length(trim(group_name)) > 0)` and the same check on `courts.name` to `schema.md`. The ERD gets a CHECK note on both columns.

**Problem:** `visitors.created_at` is not needed by any requirement in `docs/requirements.md`. No screen shows it and no report uses it. (Question 1, coverage.)
**Change:** I removed it from `schema.md` and the ERD, so every column traces to a requirement. If a later week needs to clean up old visitors, I will add it back with a migration and a requirement.

**Problem:** Nothing in the database ties `closed_at` to `status`. A ticket could be `served` with no `closed_at`, which would make the FR-13 report (left before served, per day) miss rows. (Question 4, bad data.)
**Change:** None for now. A CHECK linking the two would force every staff action to set `closed_at`, and I would rather get CRUD working first. I will set `closed_at` in the leave, serve and no show routes in Part 9 and revisit a CHECK in Week 7.

**Checked, no problem:** Position in line is computed, not stored (question 3). Each foreign key has an on purpose RESTRICT rule, so no delete can erase history except the organizer's deliberate hard delete of a mistaken ticket (question 5). Every time is `timestamptz` and group size is a number, not text (question 6). No fact is stored twice (question 2).