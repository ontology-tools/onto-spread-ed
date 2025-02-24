from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .Base import Base


class ReleaseArtifact(Base):
    __tablename__ = 'release_artifacts'

    id = Column(Integer(), primary_key=True)
    release_id = Column(Integer(), ForeignKey('releases.id'))

    local_path = Column(String())
    target_path = Column(String(), nullable=True)
    downloadable = Column(Boolean(), default=True)
    kind = Column(String(), CheckConstraint(
        "kind in ('source', 'intermediate', 'final') and (kind <> 'final' or target_path is not null)"), )

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Release(Base):
    __tablename__ = 'releases'

    id = Column(Integer, primary_key=True)
    state = Column(String(20))
    running = Column(Boolean(), default=True)
    step = Column(Integer)
    details = Column(JSON(none_as_null=True))  # Dict from step nr to step info
    start = Column(DateTime)
    started_by = Column(String())
    end = Column(DateTime)
    repo = Column(String(20))
    release_script = Column(JSON(none_as_null=True))
    worker_id = Column(String(20))
    local_dir = Column(String())

    artifacts = relationship("ReleaseArtifact", lazy="joined")

    def as_dict(self):
        val = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        val["artifacts"] = [a.as_dict() for a in self.artifacts]
        return val
