from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    access_level_id = Column(Integer, ForeignKey("access_levels.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    access_level = relationship("AccessLevel", back_populates="users")