from datetime import datetime
from typing import Any, Literal, Optional

from sqlalchemy import String, JSON, DateTime, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from .Base import Base

OPEN_STATES = {"starting", "running", "paused", "errored"}

RequestedAction = Literal["run", "skip", "rerun"]



class Release(Base):
    __tablename__ = "releases"
    __table_args__ = (
        Index(
            "uq_releases_open_repo",
            "repo",
            unique=True,
            sqlite_where=text(f"state IN ({", ".join(f"'{s}'" for s in sorted(OPEN_STATES))})"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(20))
    """Updated by the runner; the API may set 'cancelled', which runner updates must preserve."""
    start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_by: Mapped[Optional[str]] = mapped_column(String())
    end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    """When the release has fully stopped."""
    repo: Mapped[Optional[str]] = mapped_column(String(20))
    worker_id: Mapped[Optional[str]] = mapped_column(String(64))
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    requested_action: Mapped[Optional[str]] = mapped_column(String(20))
    requested_by: Mapped[Optional[str]] = mapped_column(String())
    """GitHub username of the user whose token executes the requested action."""
    context: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON(none_as_null=True))
    progress: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON(none_as_null=True))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
