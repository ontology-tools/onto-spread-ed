from sqlalchemy import Column, Integer, String

from database.Base import Base


class NextId(Base):
    __tablename__ = 'nextids'
    id = Column(Integer,primary_key=True)
    repo_name = Column(String(50))
    next_id = Column(Integer)
