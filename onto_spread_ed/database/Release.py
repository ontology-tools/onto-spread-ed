from sqlalchemy import Column, Integer, String, JSON, DateTime

from .Base import Base


class Release(Base):
    __tablename__ = 'release'

    id = Column(Integer, primary_key=True)
    state = Column(String(20))
    step = Column(Integer)
    current_info = Column(JSON(none_as_null=True))
    start = Column(DateTime)
    end = Column(DateTime)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
