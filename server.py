from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import Session, db
from models.user import User
from routes.user.controller import router as user_router
import logging
from routes.game.controller import router as game_router


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://127.0.0.1:3000"],  # React default ports
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(user_router)
app.include_router(game_router)


@app.get("/")
async def root(session: Session = Depends(db)):
    user = session.query(User).first()
    logger.info(f"User: {user}")
    return {"message": "Hello World"}
