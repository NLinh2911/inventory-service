import logging
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import asc, delete, desc, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette import status
from app.core.security import check_permissions
from app.db.base import get_db
from app.schemas.unit_of_measure import (
    UnitOfMeasureCreateRequest,
    UnitOfMeasureReadRequest,
    UnitOfMeasureUpdateRequest,
)
from app.db.models.unit_of_measure import UnitOfMeasure


db_dependency = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/unit-of-measure", tags=["Unit of Measure"])


@router.post(
    "/",
    response_model=UnitOfMeasureReadRequest,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def create_uom(db: db_dependency, uom_request: UnitOfMeasureCreateRequest):
    """
    Create a new uom in the database.
    Args:

        uom_request (UnitOfMeasureCreateRequest): The request object containing the details of the uom to create.
        - name (str): The name of the uom.
        - description (str): The description of the uom.
    Returns:

        UnitOfMeasure: The newly created uom model instance.
    Raises:

        HTTPException: If an integrity error or any other database error occurs, or if an unexpected error occurs.
    """

    try:
        uom_model = UnitOfMeasure(
            name=uom_request.name,
            abbreviation=uom_request.abbreviation,
            description=uom_request.description,
        )

        db.add(
            uom_model
        )  # create a new instance of a model that is not yet added to the session

        db.commit()
        db.refresh(uom_model)  # Refresh the new instance

        return uom_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new uom.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the new uom.",
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
    response_model=list[UnitOfMeasureReadRequest],
    status_code=status.HTTP_200_OK,
)
def read_all_uoms(
    db: db_dependency,
    limit: Optional[int] = Query(None, description="Number of records to return"),
    order_by: Optional[str] = Query(None, description="Order by column"),
    ascending: Optional[bool] = Query(True, description="Sort in ascending order"),
):
    """
    Fetch all uoms from the database along with their associated permissions.

    Args:

        limit (int, optional): The number of records to return. Defaults to None.
        order_by (str, optional): The column to order the results by. Defaults to uom_id.
        ascending (bool, optional): Sort in ascending order. Defaults to True.
        Note: the allowed columns are "uom_id", "name", and "description".
    Returns:

        list[UnitOfMeasure]: A list of UnitOfMeasure objects with their associated permissions.
    Raises:

        HTTPException: If an integrity error or any other database error occurs,
                       an HTTPException is raised with an appropriate status code
                       and error message.
    """

    try:
        allowed_columns = [
            "uom_id",
            "name",
            "abbreviation",
            "description",
        ]  # Add valid column names here

        # Start building the query
        stmt = select(UnitOfMeasure)

        # Apply ordering
        # Validate and set the order_by column or a default value
        if order_by is None:
            order_by = "uom_id"
        order_by = order_by.lower() if order_by.lower() in allowed_columns else "uom_id"
        order_column = getattr(UnitOfMeasure, order_by)
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
            detail="An error occurred while fetching all uoms.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching all uoms.",
        )


@router.get(
    "/{uom_id}",
    response_model=UnitOfMeasureReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(
            check_permissions(
                ["manage_items_INVENTORY_SERVICE", "view_items_INVENTORY_SERVICE"]
            )
        )
    ],
)
def read_uom(db: db_dependency, uom_id: int = Path(gt=0)):
    """
    Fetch a uom by its ID from the database.
    Args:

        uom_id (int): The ID of the uom to fetch. Must be greater than 0.
    Returns:

        UnitOfMeasure: The uom object if found.
    Raises:

        HTTPException: If the uom is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    """

    try:
        stmt = select(UnitOfMeasure).where(UnitOfMeasure.uom_id == uom_id)
        uom_model = db.execute(stmt).scalars().first()

        if uom_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"uom with id {uom_id} not found.",
            )

        return uom_model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while fetching the uom with id {uom_id}.",
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
            detail=f"An error occurred while fetching the uom with id {uom_id}.",
        )


@router.put(
    "/{uom_id}",
    response_model=UnitOfMeasureReadRequest,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def update_uom(
    db: db_dependency,
    uom_request: UnitOfMeasureUpdateRequest,
    uom_id: int = Path(gt=0),
):
    """
    Update an existing uom in the database.
    Args:

        uom_request (UnitOfMeasureUpdateRequest): The request object containing the fields to update.
        - name (str): The name of the uom.
        - description (str): The description of the uom.
        uom_id (int): The ID of the uom to update. Must be greater than 0.
    Returns:

        uom_model: The updated uom model.
    Raises:

        HTTPException: If the uom is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    """

    try:
        stmt = select(UnitOfMeasure).where(UnitOfMeasure.uom_id == uom_id)
        uom_model = db.execute(stmt).scalars().first()

        if uom_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"uom with id {uom_id} not found.",
            )

        # Loop through provided fields and update the corresponding fields in uom_model
        update_data = uom_request.model_dump(
            exclude_unset=True
        )  # Only get the provided fields

        for key, value in update_data.items():
            setattr(uom_model, key, value)  # Dynamically update the fields

        db.commit()
        db.refresh(uom_model)  # Refresh the updated instance
        return uom_model  # Return the updated uom model

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the uom with id {uom_id}.",
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
            detail=f"An error occurred while updating the uom with id {uom_id}.",
        )


@router.delete(
    "/{uom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_permissions(["manage_items_INVENTORY_SERVICE"]))],
)
def delete_uom(db: db_dependency, uom_id: int = Path(gt=0)):
    """
    Delete a uom from the database by its ID.
    Args:

        uom_id (int): The ID of the uom to delete. Must be greater than 0.
    Raises:

        HTTPException: If the uom is not found, or if there is an integrity error,
                       database error, or any other unexpected error.
    Returns:

        None
    """

    try:
        stmt = select(UnitOfMeasure).where(UnitOfMeasure.uom_id == uom_id)
        uom_model = db.execute(stmt).scalars().first()
        if uom_model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"uom with id {uom_id} not found.",
            )

        stmt = delete(UnitOfMeasure).where(UnitOfMeasure.uom_id == uom_id)
        db.execute(stmt)
        db.commit()

    except IntegrityError as e:
        logging.error(f"Integrity error occurred: {str(e.orig)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e.orig))
    except SQLAlchemyError as e:
        logging.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while deleting the uom with id {uom_id}.",
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
            detail=f"An error occurred while deleting the uom with id {uom_id}.",
        )
