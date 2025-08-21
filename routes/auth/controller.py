import logging
from fastapi import APIRouter, Depends
from routes.auth import services
from routes.auth.schemas import Test1Request

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/test",
    tags=["test"],
)


@router.post("/test1")
def test1(payload: Test1Request):
    logger.info(f"Getting Google auth URL")

    message = services.test1service(payload.name)
    logger.info(f"Message: {message}")
    # return RedirectResponse(url, status_code=301)
    return message


@router.get("/test2get")
def test2get(queryParam1: str, queryParam2: int):
    logger.info(f"Test2 get received: {queryParam1}, {queryParam2}")
    message = services.test2service(queryParam1, queryParam2)
    logger.info(f"Message: {message}")
    return message
