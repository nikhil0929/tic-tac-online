
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from db import Session, db
from models.user import User
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import logging
import os

from routes.user.schemas import Token, TokenData

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def create_user(session: Session, first_name: str, last_name: str, username: str, password: str):
    logger.info(f"Creating user: {first_name}, {last_name}, {username}")
    user = session.query(User).filter(User.username == username).first()
    if user:
        raise HTTPException(
            status_code=400, detail="Unable to create user: username already exists")

    hashed_password = get_password_hash(password)
    user = User(first_name=first_name, last_name=last_name,
                username=username, password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"username": user.username, "id": user.id}, expires_delta=access_token_expires
    )
    return Token(access_token=token, token_type="bearer", id=user.id)


def login(session: Session, username: str, password: str):
    user = authenticate_user(session, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username, "id": user.id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer", id=user.id)


def get_current_user(session: Session = Depends(db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        id = payload.get("id")
        if username is None or id is None:
            logger.error(f"Username or id is None: {token}")
            raise credentials_exception
        token_data = TokenData(username=username, id=id)
    except InvalidTokenError:
        logger.error(f"Invalid token: {token}")
        raise credentials_exception

    user = session.query(User).filter(
        User.username == token_data.username).first()
    logger.info(f"User: {user}")
    if user is None:
        logger.error(f"User is None: {token}")
        raise credentials_exception
    return user


### HELPER FUNCTIONS ###

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(session: Session, username: str, password: str):
    user = session.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user
