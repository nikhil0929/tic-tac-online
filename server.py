from fastapi import Depends, FastAPI
from db import Session, db
from models.user import User
from routes.user.controller import router as user_router
import logging

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

app = FastAPI()

app.include_router(user_router)


@app.get("/")
async def root(session: Session = Depends(db)):
    user = session.query(User).first()
    logger.info(f"User: {user}")
    return {"message": "Hello World"}
