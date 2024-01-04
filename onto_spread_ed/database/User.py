from sqlalchemy import Column, Integer, String

from .Base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    github_access_token = Column(String(255))
    github_id = Column(Integer)
    github_login = Column(String(255))

    def __init__(self, github_access_token, **kw: Any):
        super().__init__(**kw)
        self.github_access_token = github_access_token
