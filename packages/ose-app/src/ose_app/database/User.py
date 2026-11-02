from typing import Any

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column


from .Base import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    github_access_token: Mapped[str] = mapped_column(String(255))
    github_id: Mapped[int] = mapped_column()
    github_login: Mapped[str] = mapped_column(String(255))

    def __init__(self, github_access_token, **kw: Any):
        super().__init__(**kw)
        self.github_access_token = github_access_token
