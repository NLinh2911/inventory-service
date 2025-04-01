import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import asc, delete, desc, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from app.core.security import check_permissions
from app.db.models.item import Item
from app.db.base import get_db
from app.schemas.item import (
    ItemCreateRequest,
    ItemReadRequest,
    ItemUpdateRequest,
)
from app.db.models.item_category import ItemCategory
from app.db.models.unit_of_measure import UnitOfMeasure
from app.db.models.vendor import Vendor


router = APIRouter(prefix="/items", tags=["Items"])


db_dependency = Annotated[Session, Depends(get_db)]


@router.post(
    "/",
    response_model=ItemReadRequest,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def create_item(db: db_dependency, item_request: ItemCreateRequest):
    """
    Create a new item in the database.

    Args:

        item_request (ItemCreateRequest): The request body containing the details of the item to create.

    Returns:

        Item: The newly created item model.

    Raises:

        HTTPException: If an integrity error or any other database error occurs.
    """
    try:
        # Verify if the department, category, vendor, and unit of measure exist in the database
        models_to_check = [
            (
                ItemCategory,
                ItemCategory.category_id,
                item_request.category_id,
                "category",
            ),
            (Vendor, Vendor.vendor_id, item_request.vendor_id, "vendor"),
            (
                UnitOfMeasure,
                UnitOfMeasure.uom_id,
                item_request.unit_of_measure,
                "unit of measure",
            ),
        ]

        for model, field, value, name in models_to_check:
            stmt = select(model).where(field == value)
            result = db.execute(stmt).scalars().first()
            if result is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{name.capitalize()} with id {value} not found.",
                )

        # Create the new item
        item_model = Item(
            item_code=item_request.item_code,
            name=item_request.name,
            description=item_request.description,
            category_id=item_request.category_id,
            vendor_id=item_request.vendor_id,
            unit_of_measure=item_request.unit_of_measure,
            quantity=item_request.quantity,
            low_stock_threshold=item_request.low_stock_threshold,
        )

        db.add(
            item_model
        )  # create a new instance of a model that is not yet added to the session

        db.commit()
        db.refresh(item_model)  # Refresh the new instance

        return item_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new item.",
        )
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new item.",
        )


@router.get(
    "/",
    response_model=list[ItemReadRequest],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def read_all_items(
    db: db_dependency,
    limit: Optional[int] = Query(None, description="Number of records to return"),
    order_by: Optional[str] = Query(None, description="Order by column"),
    ascending: Optional[bool] = Query(True, description="Sort in ascending order"),
):
    """
    Fetches all items from the database.
    Args:

        limit (int, optional): The number of records to return. Defaults to None.
        order_by (str, optional): The column to order the results by. Defaults to item_id.
        ascending (bool, optional): Sort in ascending order. Defaults to True.
        Note: the allowed columns are "item_id", "item_code", "name", "description", "quantity", "low_stock_threshold","created_at", "updated_at".
    Returns:

        list[Item]: A list of Item objects retrieved from the database.
    Raises:

        HTTPException: If an integrity error or any other database error occurs,
                       or if an unexpected error occurs during the operation.
    """

    try:
        allowed_columns = [
            "item_id",
            "item_code",
            "name",
            "description",
            "quantity",
            "low_stock_threshold",
            "created_at",
            "updated_at",
        ]  # Add valid column names here

        # Start building the query
        stmt = select(Item)

        # Apply ordering
        # Validate and set the order_by column or a default value
        if order_by is None:
            order_by = "item_id"
        order_by = (
            order_by.lower() if order_by.lower() in allowed_columns else "item_id"
        )
        order_column = getattr(Item, order_by)
        if order_column:
            if ascending:
                stmt = stmt.order_by(asc(order_column))
            else:
                stmt = stmt.order_by(desc(order_column))

        # Apply limit
        if limit is not None:
            stmt = stmt.limit(limit)

        # Execute the query
        return db.execute(stmt).scalars().all()

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all items.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all items.",
        )


@router.get(
    "/id/{item_id}",
    response_model=ItemReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def read_item_by_id(db: db_dependency, item_id: int = Path(gt=0)):
    """
    Fetch a item record by its ID.
    Args:

        item_id (int): The ID of the item to fetch. Must be greater than 0.
    Returns:

        Item: The item model if found.
    Raises:

        HTTPException: If the item is not found (404), if there is an integrity error (400),
                       or if there is a general database error (500) or if an unexpected error occurs during the operation (500).
    """

    try:
        stmt = select(Item).where(Item.item_id == item_id)
        item_model = db.execute(stmt).scalars().first()

        if item_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item with id {item_id} not found.",
            )

        return item_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the item with id {item_id}.",
        )
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the item with id {item_id}.",
        )


@router.put(
    "/{item_id}",
    response_model=ItemReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def update_item(
    db: db_dependency,
    item_request: ItemUpdateRequest,
    item_id: int = Path(gt=0),
):
    """
    Update an existing item in the database.
    Args:

        item_request (ItemUpdateRequest): The request body containing the details of the item to update.
    Returns:

        Item: The updated item model.
    Raises:

        HTTPException: If the item with the given ID is not found, or if there is an integrity error or other database error.
    """
    try:
        stmt = select(Item).where(Item.item_id == item_id)
        item_model = db.execute(stmt).scalars().first()

        if item_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item with id {item_id} not found.",
            )

        # Loop through provided fields and update the corresponding fields in item_model
        update_data = item_request.model_dump(
            exclude_unset=True
        )  # Only get the provided fields

        for key, value in update_data.items():
            setattr(item_model, key, value)  # Dynamically update the fields
        db.commit()
        db.refresh(item_model)  # Refresh the updated instance
        return item_model  # Return the updated model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the item with id {item_id}.",
        )
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the item with id {item_id}.",
        )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def delete_item(db: db_dependency, item_id: int = Path(gt=0)):
    """
    Delete a item from the database.
    Args:

        item_id (int): The ID of the item to delete. Must be greater than 0.
    Raises:

        HTTPException: If the item with the given ID is not found, or if there is an integrity error or other database error.
    Returns:

        None
    """

    try:
        stmt = select(Item).where(Item.item_id == item_id)
        item_model = db.execute(stmt).scalars().first()
        if item_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item with id {item_id} not found.",
            )

        stmt = delete(Item).where(Item.item_id == item_id)
        db.execute(stmt)
        db.commit()

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the item with id {item_id}.",
        )
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the item with id {item_id}.",
        )


@router.get(
    "/low-stock",
    response_model=list[ItemReadRequest],
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def read_all_low_stock_items(
    db: db_dependency,
    limit: Optional[int] = Query(None, description="Number of records to return"),
    order_by: Optional[str] = Query(None, description="Order by column"),
    ascending: Optional[bool] = Query(True, description="Sort in ascending order"),
):
    """
    Fetches all low-stock items from the database.
    Args:

        limit (int, optional): The number of records to return. Defaults to None.
        order_by (str, optional): The column to order the results by. Defaults to item_id.
        ascending (bool, optional): Sort in ascending order. Defaults to True.
        Note: the allowed columns are "item_id", "item_code", "name", "description", "quantity", "low_stock_threshold","created_at", "updated_at".
    Returns:

        list[Item]: A list of Item objects that has their quantity < their low stock threshold retrieved from the database.
    Raises:

        HTTPException: If an integrity error or any other database error occurs,
                       or if an unexpected error occurs during the operation.
    """

    try:
        allowed_columns = [
            "item_id",
            "item_code",
            "name",
            "description",
            "quantity",
            "low_stock_threshold",
            "created_at",
            "updated_at",
        ]  # Add valid column names here

        # Start building the query
        stmt = select(Item).where(Item.quantity < Item.low_stock_threshold)

        # Apply ordering
        # Validate and set the order_by column or a default value
        if order_by is None:
            order_by = "item_id"
        order_by = (
            order_by.lower() if order_by.lower() in allowed_columns else "item_id"
        )
        order_column = getattr(Item, order_by)
        if order_column:
            if ascending:
                stmt = stmt.order_by(asc(order_column))
            else:
                stmt = stmt.order_by(desc(order_column))

        # Apply limit
        if limit is not None:
            stmt = stmt.limit(limit)

        # Execute the query
        return db.execute(stmt).scalars().all()

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all low-stock items.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all low-stock items.",
        )


@router.patch(
    "/{item_id}",
    response_model=ItemReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "deduct_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def deduct_quantity(
    db: db_dependency,
    change_quantity: int = Query(
        gt=0, description="Quantity to deduct, must be greater than 0"
    ),
    item_id: int = Path(gt=0),
):
    """
    Modify the quantity of an item in the database.
    Args:

        item_request (ItemModifyQuantityRequest): The request body containing the details of the item to update.
    Returns:

        Item: The updated item model.
    Raises:

        HTTPException: If the item with the given ID is not found, or if there is an integrity error or other database error.
    """
    try:
        stmt = select(Item).where(Item.item_id == item_id)
        item_model = db.execute(stmt).scalars().first()

        if item_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item with id {item_id} not found.",
            )

        if item_model.quantity < change_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient quantity in stock.",
            )
        print(item_model.quantity, change_quantity)
        # Update the quantity of the item
        item_model.quantity -= change_quantity
        # Update the item model with the new quantity

        db.commit()
        db.refresh(item_model)  # Refresh the updated instance
        return item_model  # Return the updated model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the item with id {item_id}.",
        )
    except HTTPException as e:
        logging.error(f"HTTPException: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the item with id {item_id}.",
        )
