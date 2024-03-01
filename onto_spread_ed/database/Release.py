from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean

from .Base import Base


class Release(Base):
    __tablename__ = 'release'

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

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
