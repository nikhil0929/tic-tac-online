from pydantic import BaseModel, Field
import enum


class GameMessageType(str, enum.Enum):
    GAME_START = "GAME_START"
    GAME_MOVE = "GAME_MOVE"
    GAME_END = "GAME_END"


class Leaderboard(BaseModel):
    user_id: int
    username: str
    wins: int
    losses: int
    draws: int
    efficiency: float
