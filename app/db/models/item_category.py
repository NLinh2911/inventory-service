from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ItemCategory(Base):
    __tablename__ = "item_categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))

    # Created at timestamp
    created_at = Column(DateTime, server_default=func.now())

    # Updated at timestamp
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    items = relationship("Item", back_populates="item_category")

    def __repr__(self):
        return f"<ItemCategory(id={self.category_id}, name='{self.name}', description='{self.description}')>"
