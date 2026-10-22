# Self review of personas and wireframes

I reviewed each screen at phone and laptop width against my two personas, Jerich (player) and Lara (organizer), and against my "Because ..., my interface must ..." rules in `personas.md`.

## Join the queue (Jerich, FR-01)

**Works well:** The form asks for only a name and a court, with one large Get a ticket button. This follows my rule that Jerich joins in a hurry with one hand, so there is little to type and the button is easy to hit.

**Problem:** The court selector gives no clue which court is busy. Jerich has to pick Court 1, 2 or 3 without knowing how many groups are waiting on each, which breaks visibility of system status. He could join the longest line by accident and only find out on the next screen.

**Change:** I will show the waiting count inside each option, for example "Court 1 (1 group waiting)", so he can compare courts before he joins. This is a small change to the selector in both the phone and laptop frames.

## My place (Jerich, FR-02 and FR-03)

**Works well:** The court, ticket number, status and position are stacked from most to least important, and the ticket number is very large. This follows my rule that the order must be the biggest and clearest thing on the screen, so Jerich can read it in sunlight at a glance.

**Problem:** When Jerich is called, the screen looks almost the same as when he is waiting, since only the word in the badge changes. He may be looking at the court or his friends and miss it. This breaks visibility of system status at the most important moment of the visit.

**Change:** I will add a Called state to the frame, with a bold banner at the top that says "Go to Court 2 now" and a stronger badge, and the position sentence will be replaced by that message. The Waiting state stays as drawn. I will also keep the status in words and not only color.

## Staff dashboard (Lara, FR-04, FR-05 and FR-06)

**Works well:** Call next is large and sits near the top, and the waiting count per court sits just above the list. This follows my rule that Lara, who is often standing and interrupted, needs the most common action to be the easiest to reach, and that she can see all courts at a glance.

**Problem:** Call next sits next to a court filter set to "All courts", so it is unclear which court it calls. Lara could call a group on the wrong court, which hurts error prevention, and a mistaken call is unfair to players because they are told to move to a court that is not free. The Serve button also appears on groups who have not been called yet, which lets her skip a step by accident.

**Change:** I will make Call next work for one court at a time, either by showing a Call next button on each court's count or by disabling it until a court is chosen in the filter. I will also show Serve only on called rows and show Call on waiting rows, so the buttons match the group's status. I will fix the waiting count for Court 1 so it matches the list.

## Wireframe updates

I will update the join, My place and staff frames with the changes above before I start building. The words on the frames (court, ticket, groups, no show) match how players talk on the court, so I kept them.