import logging

from sqlalchemy.orm import Session
from db import db
from fastapi import APIRouter, Depends
from models.user import User
from routes.user.services import get_current_user, create_user, login
from routes.user.schemas import CreateUserRequest, LoginRequest

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/user",
    tags=["user"],
)


@router.get("/")
def get_current_user(
    user: User = Depends(get_current_user),
):
    return user


@router.post("/create")
def create_new_user(payload: CreateUserRequest, session: Session = Depends(db)):
    logger.info(f"Getting Google auth URL")

    message = create_user(
        session=session,
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        password=payload.password,
    )
    logger.info(f"Message: {message}")
    # return RedirectResponse(url, status_code=301)
    return message


@router.post("/login")
def login_user(payload: LoginRequest, session: Session = Depends(db)):
    logger.info(f"Login received: {payload}")

    message = login(session=session,
                    username=payload.username,
                    password=payload.password)
    logger.info(f"Message: {message}")
    return message
