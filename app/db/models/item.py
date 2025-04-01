from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    item_code = Column(String(20), index=True, nullable=False)
    name = Column(String(100), index=True, nullable=False)
    description = Column(String(255), index=True)
    category_id = Column(
        Integer, ForeignKey("item_categories.category_id"), nullable=False
    )

    vendor_id = Column(Integer, ForeignKey("vendors.vendor_id"))

    # Unit of measure for the item (e.g., pieces, kilograms, liters)
    unit_of_measure = Column(
        Integer, ForeignKey("unit_of_measures.uom_id"), nullable=False
    )

    quantity = Column(Integer, default=0, nullable=False)

    # Threshold to trigger low stock alerts
    low_stock_threshold = Column(Integer, default=0)

    # Created at timestamp
    created_at = Column(DateTime, server_default=func.now())

    # Updated at timestamp
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships

    item_category = relationship("ItemCategory", back_populates="items")
    vendor = relationship("Vendor", back_populates="items")
    uom = relationship("UnitOfMeasure", back_populates="items")
