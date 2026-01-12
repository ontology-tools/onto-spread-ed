from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, mapped_column

from .Base import Base


class ReleaseArtifact(Base):
    __tablename__ = 'release_artifacts'

    id = mapped_column(Integer(), primary_key=True)
    release_id = mapped_column(Integer(), ForeignKey('releases.id'))

    local_path = mapped_column(String())
    target_path = mapped_column(String(), nullable=True)
    downloadable = mapped_column(Boolean(), default=True)
    kind = mapped_column(String(), CheckConstraint(
        "kind in ('source', 'intermediate', 'final') and (kind <> 'final' or target_path is not null)"), )

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Release(Base):
    __tablename__ = 'releases'

    id = mapped_column(Integer, primary_key=True)
    state = mapped_column(String(20))
    running = mapped_column(Boolean(), default=True)
    step = mapped_column(Integer)
    details = mapped_column(JSON(none_as_null=True))  # Dict from step nr to step info
    start = mapped_column(DateTime)
    started_by = mapped_column(String())
    end = mapped_column(DateTime)
    repo = mapped_column(String(20))
    release_script = mapped_column(JSON(none_as_null=True))
    worker_id = mapped_column(String(20))
    local_dir = mapped_column(String())

    artifacts = relationship("ReleaseArtifact", lazy="joined")

    def as_dict(self):
        val = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        val["artifacts"] = [a.as_dict() for a in self.artifacts]
        return val
