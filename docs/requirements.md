# PivotPB requirements

**Setting:** Open play pickleball at three courts, weekday evenings
**People who wait:** Players who join a court's line in groups of 2 or 4 (see Jerich in [docs/week3/personas.md](week3/personas.md))
**People who serve:** The volunteer organizer who runs open play (see Lara in [docs/week3/personas.md](week3/personas.md))

**Problem statement:** A player waiting for a court needs a way to see their real place in line without guarding a paddle, because a paddle stack can be shuffled and hides how many groups are ahead.

## Functional requirements

| ID | Requirement | Priority | Stores data? | Status |
| --- | --- | --- | --- | --- |
| FR-01 | A player can join the line for a court by entering their name. | Must | **Yes** | Built (Week 3) |
| FR-02 | A player can see their ticket code, status and how many groups are ahead of them. | Must | **Yes** | Built (Week 3) |
| FR-03 | A player can leave the line before or after being called. | Must | **Yes** | Built (Week 3) |
| FR-04 | An organizer can see each court's waiting list in the order groups joined. | Must | **Yes** | Built (Week 3) |
| FR-05 | An organizer can call the next group, mark a group as served, or mark a group as no show. | Must | **Yes** | Built (Week 3) |
| FR-06 ★ | An organizer can see how many groups are waiting on each court. | Should | **Yes** | Built (Week 3) |
| FR-07 ★ | A player chooses whether their group has 2 or 4 players when joining. | Must | **Yes** | Built (Week 3) |
| FR-08 ★ | Every court has its own ticket numbers, shown as a code such as C1-011. | Must | **Yes** | Built (Week 3) |
| FR-09 | A player who is on several courts can see all their active tickets and cannot hold two active tickets on the same court. | Should | **Yes** | Built (Week 3) |
| FR-10 | My place updates by itself and shows when the group is called, without a refresh. | Must | No | Built (Week 3) |
| FR-11 | An organizer can add, rename and switch off a court. | Must | **Yes** | This week |
| FR-12 | An organizer can delete a ticket created by mistake. | Should | **Yes** | This week |
| FR-13 ★ | An organizer can see how many groups left before being served, per court, per day. | Should | **Yes** | Later |
| FR-14 | A player can switch the page to a larger text size. | Could | No | Later |

## Non-functional requirements

| ID | Requirement | Category | Priority |
| --- | --- | --- | --- |
| NFR-01 | No ticket is lost when Flask, Docker or the database restarts. | Reliability | Must |
| NFR-02 | Two groups can never get the same ticket number on the same court, even if they tap Join at the same moment. | Data integrity | Must |
| NFR-03 | My place loads in under 2 seconds on slow mobile data. | Performance | Should |
| NFR-04 | Every screen scores 90 or higher in the Lighthouse accessibility check. | Accessibility | Must |
| NFR-05 | No password or secret key is stored in the repository. | Security | Must |
| NFR-06 | Status text keeps a contrast ratio of at least 4.5 to 1 so it stays readable in sunlight. | Accessibility | Should |

## MVP

**MVP:** FR-01 to FR-05, FR-07, FR-08, FR-10, FR-11, NFR-01, NFR-02, NFR-04 and NFR-05. This is the smallest version that replaces the paddle stack, because players can join and see a trustworthy place in line, and the organizer can move the line forward on a database that never forgets a ticket.

**Out of scope this semester:**
- Text or push notifications when a group is called, because they need an outside service and the page already updates itself.
- Court booking for a fixed time, because PivotPB is for open play where nobody reserves a slot.

## Feedback from a real person

| Who (role only, no full name) | What they said | What I changed |
| --- | --- | --- |
| Player | "The design on your ticket seems a bit off. I can't say exactly, but I feel like there is something wrong"| I fixed the flawed design of a button (before editng, the button seemed like a notification rather than a button)| |