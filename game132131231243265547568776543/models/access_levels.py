from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from database.db import Base


class AccessLevel(Base):
    __tablename__ = "access_levels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)

    users = relationship("User", back_populates="access_level")