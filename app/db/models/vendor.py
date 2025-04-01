from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    vendor_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))

    # Created at timestamp
    created_at = Column(DateTime, server_default=func.now())

    # Updated at timestamp
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    items = relationship("Item", back_populates="vendor")

    def __repr__(self):
        return f"<Vendor(id={self.vendor_id}, name='{self.name}', description='{self.description}')>"
