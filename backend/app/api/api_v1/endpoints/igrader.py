from typing import Any

from fastapi import APIRouter, status

from app import schemas

router = APIRouter()


@router.post("", response_model=schemas.IGrader, status_code=status.HTTP_201_CREATED)
def create_igrader() -> Any:
    pass
