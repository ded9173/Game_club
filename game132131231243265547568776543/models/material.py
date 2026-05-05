from sqlalchemy import Column, Integer, String, Numeric
from database.db import Base


class Material(Base):
    __tablename__ = "materials"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=False)
    consumption_norm = Column(Numeric(precision=10, scale=4), nullable=False)
    cost_per_unit = Column(Numeric(precision=10, scale=2), nullable=False)

    def __repr__(self):
        return f"<Material(id={self.id}, name='{self.name}', cost={self.cost_per_unit})>"