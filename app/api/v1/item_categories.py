import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import asc, delete, desc, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from app.core.security import check_permissions
from app.db.base import get_db
from app.schemas.item_category import (
    ItemCategoryCreateRequest,
    ItemCategoryReadRequest,
    ItemCategoryUpdateRequest,
)
from app.db.models.item_category import ItemCategory


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/item-categories", tags=["Item Categories"])


@router.post(
    "/",
    response_model=ItemCategoryReadRequest,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def create_item_category(
    db: db_dependency, item_category_request: ItemCategoryCreateRequest
):
    """
    Create a new item category in the database.
    Args:

        item_category_request (ItemCategoryCreateRequest): The request object containing the details of the item category to create.
        - name (str): The name of the item category. Must be unique.
        - description (str): The description of the item category.
    Returns:

        ItemCategory: The newly created item category model instance.
    Raises:

        HTTPException: If an integrity error or any other database error occurs, or if an unexpected error occurs.
    """

    try:
        item_categories_model = ItemCategory(
            name=item_category_request.name,
            description=item_category_request.description,
        )

        db.add(
            item_categories_model
        )  # create a new instance of a model that is not yet added to the session

        db.commit()
        db.refresh(item_categories_model)  # Refresh the new instance

        return item_categories_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new item category.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new item category.",
        )


@router.get(
    "/",
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
    response_model=list[ItemCategoryReadRequest],
    status_code=status.HTTP_200_OK,
)
def read_all_item_categories(
    db: db_dependency,
    limit: Optional[int] = Query(None, description="Number of records to return"),
    order_by: Optional[str] = Query(None, description="Order by column"),
    ascending: Optional[bool] = Query(True, description="Sort in ascending order"),
):
    """
    Fetch all item categories from the database.

    Args:

        limit (int, optional): The number of records to return. Defaults to None.
        order_by (str, optional): The column to order the results by. Defaults to category_id.
        ascending (bool, optional): Sort in ascending order. Defaults to True.
        Note: the allowed columns are "category_id", "name", and "description".
    Returns:

        list[ItemCategory]: A list of ItemCategory objects.
    Raises:

        HTTPException: If an integrity error or any other database error occurs,
                       an HTTPException is raised with an appropriate status code
                       and error message.
    """

    try:
        allowed_columns = [
            "category_id",
            "name",
            "description",
        ]  # Add valid column names here

        # Start building the query
        stmt = select(ItemCategory)

        # Apply ordering
        # Validate and set the order_by column or a default value
        if order_by is None:
            order_by = "category_id"
        order_by = (
            order_by.lower() if order_by.lower() in allowed_columns else "category_id"
        )
        order_column = getattr(ItemCategory, order_by)
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
        logging.error(f"Integrity error occurred: {str(e.orig)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all item categories.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all item categories.",
        )


@router.get(
    "/{category_id}",
    response_model=ItemCategoryReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def read_item_categories(db: db_dependency, category_id: int = Path(gt=0)):
    """
    Fetch a item category by its ID from the database.
    Args:

        category_id (int): The ID of the item category to fetch. Must be greater than 0.
    Returns:

        ItemCategory: The item category object if found.
    Raises:

        HTTPException: If the item category is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    """

    try:
        stmt = select(ItemCategory).where(ItemCategory.category_id == category_id)
        item_categories_model = db.execute(stmt).scalars().first()

        if item_categories_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item category with id {category_id} not found.",
            )

        return item_categories_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the item category with id {category_id}.",
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
            detail=f"An error occurred while fetching the item category with id {category_id}.",
        )


@router.put(
    "/{category_id}",
    response_model=ItemCategoryReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def update_item_categories(
    db: db_dependency,
    item_category_request: ItemCategoryUpdateRequest,
    category_id: int = Path(gt=0),
):
    """
    Update an existing item category in the database.
    Args:

        item_category_request (ItemCategoryUpdateRequest): The request object containing the fields to update.
        - name (str): The name of the item category.
        - description (str): The description of the item category.
        category_id (int): The ID of the item category to update. Must be greater than 0.
    Returns:

        item_categories_model: The updated item category model.
    Raises:

        HTTPException: If the item category is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    """

    try:
        stmt = select(ItemCategory).where(ItemCategory.category_id == category_id)
        item_categories_model = db.execute(stmt).scalars().first()

        if item_categories_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item category with id {category_id} not found.",
            )

        # Loop through provided fields and update the corresponding fields in item_categories_model
        update_data = item_category_request.model_dump(
            exclude_unset=True
        )  # Only get the provided fields

        for key, value in update_data.items():
            setattr(item_categories_model, key, value)  # Dynamically update the fields

        db.commit()
        db.refresh(item_categories_model)  # Refresh the updated instance
        return item_categories_model  # Return the updated item category model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the item category with id {category_id}.",
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
            detail=f"An error occurred while updating the item category with id {category_id}.",
        )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def delete_item_categories(db: db_dependency, category_id: int = Path(gt=0)):
    """
    Delete a item category from the database by its ID.
    Args:

        category_id (int): The ID of the item category to delete. Must be greater than 0.
    Raises:

        HTTPException: If the item category is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    Returns:

        None
    """

    try:
        stmt = select(ItemCategory).where(ItemCategory.category_id == category_id)
        item_categories_model = db.execute(stmt).scalars().first()
        if item_categories_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"item category with id {category_id} not found.",
            )

        stmt = delete(ItemCategory).where(ItemCategory.category_id == category_id)
        db.execute(stmt)
        db.commit()

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e.orig)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the item category with id {category_id}.",
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
            detail=f"An error occurred while deleting the item category with id {category_id}.",
        )
