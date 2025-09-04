
import json
import logging
import uuid

from sqlalchemy.orm import Session
from db import db
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
import redis

from models.user import User
from routes.game.schemas import GameMessageType, Leaderboard
from routes.game.services import GameManager, create_websocket_token, get_current_user_from_websocket_token, leaderboard
from routes.user.services import get_current_user

logger = logging.getLogger(__name__)

# Dependency function to get redis client


def get_redis_client():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)


router = APIRouter(
    prefix="/game",
    tags=["game"],
)

manager = GameManager()


@router.post("/websocket-token")
def get_websocket_token(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Exchange JWT for a temporary WebSocket token"""
    websocket_token = create_websocket_token(current_user, redis_client)
    logger.info(f"WebSocket token: {websocket_token}")
    print(f"WebSocket token: {websocket_token}")

    return {"websocket_token": websocket_token}


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session: Session = Depends(db),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    await websocket.accept()

    # Extract token from query parameters
    query_params = websocket.query_params
    token = query_params.get("token")

    print("Connected to websocket")

    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    print(f"Token ISSS: {token}")

    user = get_current_user_from_websocket_token(
        token=token, session=session, redis_client=redis_client)
    print(f"User: {user}")
    await manager.connect(user.id, websocket)
    await manager.join_queue(session, user.id)

    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == GameMessageType.GAME_MOVE.value:
                # Handle game move
                await manager.play_move(
                    session,
                    data["game_id"],
                    user.id,
                    data["row"],
                    data["col"]
                )
    except WebSocketDisconnect:
        manager.disconnect(user.id)
    # except Exception as e:
    #     await websocket.close(code=4001, reason=f"Invalid token: {str(e)}")


@router.get("/leaderboard")
def get_leaderboard(session: Session = Depends(db)):
    ldr_board = leaderboard(session)
    return ldr_board
