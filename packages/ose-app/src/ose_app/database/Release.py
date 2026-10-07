from datetime import datetime
from typing import Any, Optional

from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .Base import Base

OPEN_STATES = {"starting", "running", "paused", "errored"}


class Release(Base):
    __tablename__ = 'releases'

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(20))
    """Mirrors the state of the context, except that a cancellation by a user is set here first"""
    start: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_by: Mapped[Optional[str]] = mapped_column(String())
    end: Mapped[Optional[datetime]] = mapped_column(DateTime)
    repo: Mapped[Optional[str]] = mapped_column(String(20))
    worker_id: Mapped[Optional[str]] = mapped_column(String(20))
    """Identifies the process and thread running the release, if one does"""
    context: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON(none_as_null=True))
    """The serialised `ReleaseContext` of the build"""
    progress: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON(none_as_null=True))
    """The latest progress of the running stage"""

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
