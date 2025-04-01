from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.vendor import Vendor
from app.db.models.item import Item
from app.db.models.item_category import ItemCategory
from app.db.models.unit_of_measure import UnitOfMeasure
from app.core.config import settings

# Define your database URL
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URL)

# Create the database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

# Initialize sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize some initial data
initial_data = {
    "item_category": [
        {"name": "Electronics", "description": "Devices and gadgets"},
        {"name": "Furniture", "description": "Home and office furniture"},
        {"name": "Clothing", "description": "Apparel and garments"},
    ],
    "unit_of_measure": [
        {"name": "Piece", "description": "Individual unit", "abbreviation": "pc"},
        {"name": "Kilogram", "description": "Weight measurement", "abbreviation": "kg"},
        {"name": "Liter", "description": "Volume measurement", "abbreviation": "l"},
    ],
    "vendor": [
        {"name": "Vendor A", "description": "Primary electronics supplier"},
        {"name": "Vendor B", "description": "Furniture supplier"},
        {"name": "Vendor C", "description": "Clothing supplier"},
    ],
    "item": [
        {
            "name": "Smartphone",
            "item_code": "ELEC001",
            "description": "A high-end smartphone",
            "quantity": 50,
            "low_stock_threshold": 10,
            "category": "Electronics",
            "vendor": "Vendor A",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Laptop",
            "item_code": "ELEC002",
            "description": "A powerful laptop",
            "quantity": 30,
            "low_stock_threshold": 5,
            "category": "Electronics",
            "vendor": "Vendor A",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Headphones",
            "item_code": "ELEC003",
            "description": "Noise-cancelling headphones",
            "quantity": 100,
            "low_stock_threshold": 20,
            "category": "Electronics",
            "vendor": "Vendor A",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Sofa",
            "item_code": "FURN001",
            "description": "A comfortable sofa",
            "quantity": 15,
            "low_stock_threshold": 3,
            "category": "Furniture",
            "vendor": "Vendor B",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Dining Table",
            "item_code": "FURN002",
            "description": "A wooden dining table",
            "quantity": 10,
            "low_stock_threshold": 2,
            "category": "Furniture",
            "vendor": "Vendor B",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Chair",
            "item_code": "FURN003",
            "description": "A sturdy chair",
            "quantity": 50,
            "low_stock_threshold": 10,
            "category": "Furniture",
            "vendor": "Vendor B",
            "unit_of_measure": "Piece",
        },
        {
            "name": "T-Shirt",
            "item_code": "CLOT001",
            "description": "A cotton t-shirt",
            "quantity": 200,
            "low_stock_threshold": 50,
            "category": "Clothing",
            "vendor": "Vendor C",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Jeans",
            "item_code": "CLOT002",
            "description": "A pair of denim jeans",
            "quantity": 150,
            "low_stock_threshold": 30,
            "category": "Clothing",
            "vendor": "Vendor C",
            "unit_of_measure": "Piece",
        },
        {
            "name": "Jacket",
            "item_code": "CLOT003",
            "description": "A warm jacket",
            "quantity": 100,
            "low_stock_threshold": 20,
            "category": "Clothing",
            "vendor": "Vendor C",
            "unit_of_measure": "Piece",
        },
    ],
}


# Helper function
def create_vendor(db_session):
    # loop through initial data and create vendor objects
    for vendor_data in initial_data["vendor"]:
        vendor = Vendor(**vendor_data)
        db_session.add(vendor)
    db_session.commit()


def create_item_category(db_session):
    # loop through initial data and create item category objects
    for category_data in initial_data["item_category"]:
        category = ItemCategory(**category_data)
        db_session.add(category)
    db_session.commit()


def create_unit_of_measure(db_session):
    # loop through initial data and create unit of measure objects
    for uom_data in initial_data["unit_of_measure"]:
        uom = UnitOfMeasure(**uom_data)
        db_session.add(uom)
    db_session.commit()


def create_items(db_session):
    # loop through initial data and create item objects
    for item_data in initial_data["item"]:
        # Fetch related objects by name
        category_id = db_session.execute(
            select(ItemCategory.category_id).where(
                ItemCategory.name == item_data["category"]
            )
        ).scalar_one_or_none()
        vendor_id = db_session.execute(
            select(Vendor.vendor_id).where(Vendor.name == item_data["vendor"])
        ).scalar_one_or_none()
        uom_id = db_session.execute(
            select(UnitOfMeasure.uom_id).where(
                UnitOfMeasure.name == item_data["unit_of_measure"]
            )
        ).scalar_one_or_none()

        # Create the item object with relationships
        item = Item(
            name=item_data["name"],
            item_code=item_data["item_code"],
            description=item_data["description"],
            quantity=item_data["quantity"],
            low_stock_threshold=item_data["low_stock_threshold"],
            category_id=category_id,
            vendor_id=vendor_id,
            unit_of_measure=uom_id,
        )
        db_session.add(item)
    db_session.commit()


# Main function to initialize DB and data
def initialize_db():
    # Create the database schema if it doesn't exist
    Base.metadata.create_all(bind=engine)

    # Open a session to interact with the database
    db_session = SessionLocal()
    try:
        # Check if the database is already initialized
        existing_item = db_session.query(Item).first()
        if existing_item:
            print("Existing item found:", existing_item.name)
            return False  # Database is already initialized

        # Insert default users or data here
        print("Initializing database with default values...")

        # Create initial data
        create_vendor(db_session)
        create_item_category(db_session)
        create_unit_of_measure(db_session)
        create_items(db_session)

        return True  # Database initialized successfully
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return False
    finally:
        db_session.close()


if __name__ == "__main__":
    if initialize_db():
        print("Database initialized and initial data seeded successfully.")
    else:
        print("Database already initialized. Skipping initDB.")
