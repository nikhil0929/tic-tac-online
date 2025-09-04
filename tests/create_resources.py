"""
Test resource creation utilities for tic-tac-toe backend tests
"""

import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models.user import User
from models.game import Game, GameStatus
from routes.user.services import get_password_hash


def create_test_user(
    session: Session,
    first_name: str = "Test",
    last_name: str = "User",
    username: str = None,
    password: str = "testpass123",
    wins: int = 0,
    losses: int = 0,
    draws: int = 0,
    is_active: bool = True
) -> User:
    """Create a test user and add to database"""
    if username is None:
        username = f"testuser_{uuid.uuid4().hex[:8]}"

    hashed_password = get_password_hash(password)

    user = User(
        first_name=first_name,
        last_name=last_name,
        username=username,
        password=hashed_password,
        wins=wins,
        losses=losses,
        draws=draws,
        is_active=is_active
    )

    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_test_game(
    session: Session,
    player1: User = None,
    player2: User = None,
    status: GameStatus = GameStatus.IN_PROGRESS,
    winner_id: int = None,
    loser_id: int = None,
    is_draw: bool = False,
    player1_move_count: int = 0,
    player2_move_count: int = 0,
    final_state: str = None,
    created_at: datetime = None
) -> Game:
    """Create a test game and add to database"""

    # Create default users if not provided
    if player1 is None:
        player1 = create_test_user(
            session, username=f"player1_{uuid.uuid4().hex[:8]}")
    if player2 is None:
        player2 = create_test_user(
            session, username=f"player2_{uuid.uuid4().hex[:8]}")

    if final_state is None:
        # Default empty board
        final_state = json.dumps([[None, None, None] for _ in range(3)])

    game = Game(
        player1_id=player1.id,
        player2_id=player2.id,
        status=status,
        winner_id=winner_id,
        loser_id=loser_id,
        is_draw=is_draw,
        player1_move_count=player1_move_count,
        player2_move_count=player2_move_count,
        final_state=final_state,
        created_at=created_at or datetime.now(),
        updated_at=created_at or datetime.now()
    )

    session.add(game)
    session.commit()
    session.refresh(game)
    return game


def create_completed_game(
    session: Session,
    player1: User = None,
    player2: User = None,
    winner: User = None,
    is_draw: bool = False,
    player1_moves: int = 5,
    player2_moves: int = 4
) -> Game:
    """Create a completed game with winner/loser set"""

    if player1 is None:
        player1 = create_test_user(
            session, username=f"player1_{uuid.uuid4().hex[:8]}")
    if player2 is None:
        player2 = create_test_user(
            session, username=f"player2_{uuid.uuid4().hex[:8]}")

    winner_id = None
    loser_id = None

    if not is_draw and winner is not None:
        winner_id = winner.id
        loser_id = player2.id if winner.id == player1.id else player1.id

    # Create a realistic final board state
    if is_draw:
        final_board = [
            [player1.id, player2.id, player1.id],
            [player2.id, player1.id, player2.id],
            [player2.id, player1.id, player2.id]
        ]
    elif winner_id == player1.id:
        final_board = [
            [player1.id, player1.id, player1.id],  # Winning row
            [player2.id, player2.id, None],
            [None, None, None]
        ]
    else:
        final_board = [
            [player2.id, player2.id, player2.id],  # Winning row
            [player1.id, player1.id, None],
            [None, None, None]
        ]

    return create_test_game(
        session=session,
        player1=player1,
        player2=player2,
        status=GameStatus.COMPLETED,
        winner_id=winner_id,
        loser_id=loser_id,
        is_draw=is_draw,
        player1_move_count=player1_moves,
        player2_move_count=player2_moves,
        final_state=json.dumps(final_board)
    )


def cleanup_test_data(session: Session):
    """Clean up all test data from database"""
    # Delete games first due to foreign key constraints
    session.query(Game).delete()
    session.query(User).delete()
    session.commit()


def create_multiple_test_users(session: Session, count: int) -> list[User]:
    """Create multiple test users for bulk testing"""
    users = []
    for i in range(count):
        user = create_test_user(
            session=session,
            first_name=f"User{i+1}",
            last_name=f"Test{i+1}",
            username=f"testuser{i+1}_{uuid.uuid4().hex[:6]}",
            wins=i,
            losses=max(0, i-1),
            draws=max(0, i-2)
        )
        users.append(user)
    return users


def create_leaderboard_test_data(session: Session) -> list[User]:
    """Create test data specifically for leaderboard testing"""
    users = []

    # High-performing user
    user1 = create_test_user(
        session, "Alice", "Winner", f"alice_{uuid.uuid4().hex[:6]}",
        wins=10, losses=2, draws=1
    )
    users.append(user1)

    # Medium-performing user
    user2 = create_test_user(
        session, "Bob", "Average", f"bob_{uuid.uuid4().hex[:6]}",
        wins=5, losses=5, draws=3
    )
    users.append(user2)

    # Low-performing user with enough games
    user3 = create_test_user(
        session, "Charlie", "Beginner", f"charlie_{uuid.uuid4().hex[:6]}",
        wins=1, losses=8, draws=2
    )
    users.append(user3)

    # User with insufficient games (should not appear in leaderboard)
    user4 = create_test_user(
        session, "Dave", "New", f"dave_{uuid.uuid4().hex[:6]}",
        wins=1, losses=1, draws=0
    )
    users.append(user4)

    # Create some games for efficiency calculation
    for user in users[:3]:  # Only for users with enough games
        for _ in range(3):
            create_completed_game(
                session=session,
                player1=user,
                winner=user if user.wins > 0 else None,
                player1_moves=4,
                player2_moves=3
            )

    return users
