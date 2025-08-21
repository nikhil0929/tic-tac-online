import enum
from datetime import date, datetime
from decimal import Decimal
from typing import List
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from models.base import Base


class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(
        Date(), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(15), nullable=True)

    # Numeric types
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    salary: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True)

    # Text types
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Date/Time types
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)

    # Enum type
    gender: Mapped[Optional[Gender]] = mapped_column(
        Enum(Gender, name='gender'), nullable=True)

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.first_name!r} {self.last_name!r}, email={self.email!r})"
