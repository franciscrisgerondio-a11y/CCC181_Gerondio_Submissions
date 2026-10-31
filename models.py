import uuid
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (CheckConstraint, DateTime, ForeignKey, Index, SmallInteger,
                        String, UniqueConstraint, func, text)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class Court(db.Model):
    __tablename__ = "courts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="court")

    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_courts_name_not_blank"),
    )


class Visitor(db.Model):
    __tablename__ = "visitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True,
        default=uuid.uuid4, server_default=text("gen_random_uuid()"),
    )

    tickets: Mapped[list["Ticket"]] = relationship(back_populates="visitor")


class Ticket(db.Model):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id", ondelete="RESTRICT"))
    visitor_id: Mapped[int] = mapped_column(ForeignKey("visitors.id", ondelete="RESTRICT"))
    number: Mapped[int]
    group_name: Mapped[str] = mapped_column(String(50))
    players: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(20), default="waiting", server_default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    court: Mapped["Court"] = relationship(back_populates="tickets")
    visitor: Mapped["Visitor"] = relationship(back_populates="tickets")

    __table_args__ = (
        UniqueConstraint("court_id", "number", name="uq_tickets_court_number"),
        Index("uq_tickets_one_active_per_court", "visitor_id", "court_id",
              unique=True, postgresql_where=text("status IN ('waiting', 'called')")),
        CheckConstraint("number > 0", name="ck_tickets_number_positive"),
        CheckConstraint("players IN (2, 4)", name="ck_tickets_players"),
        CheckConstraint("length(trim(group_name)) > 0", name="ck_tickets_group_name_not_blank"),
        CheckConstraint(
            "status IN ('waiting', 'called', 'served', 'no-show', 'left')",
            name="ck_tickets_status",
        ),
    )