import enum
from datetime import date, datetime
from decimal import Decimal
from typing import List
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from models.base import Base
from sqlalchemy.dialects.postgresql import JSONB


class GameStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Game(Base):
    __tablename__ = "game"
    id: Mapped[int] = mapped_column(primary_key=True)
    player1_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)
    player2_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=False)
    final_state: Mapped[str] = mapped_column(JSONB, nullable=True)
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now)
    is_draw: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False)
    winner_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=True)
    loser_id: Mapped[int] = mapped_column(
        ForeignKey("user.id"), nullable=True)
    player1_move_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)
    player2_move_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"Game(id={self.id!r}, player1_id={self.player1_id!r}, player2_id={self.player2_id!r}, status={self.status!r}, created_at={self.created_at!r}, updated_at={self.updated_at!r}, is_draw={self.is_draw!r}, winner_id={self.winner_id!r}, loser_id={self.loser_id!r}, player1_move_count={self.player1_move_count!r}, player2_move_count={self.player2_move_count!r})"
