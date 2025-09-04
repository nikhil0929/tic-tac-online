from collections import deque
import json
import logging
import random
import uuid

from sqlalchemy import func, case
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, WebSocket
from db import db
from models.game import Game, GameStatus
from models.user import User
from routes.game.schemas import GameMessageType
import redis

logger = logging.getLogger(__name__)

# Dependency function to get redis client

LEADERBOARD_MIN_GAMES = 3


def get_redis_client():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)


class GameManager:
    def __init__(self):
        self.queue = deque([])  # item = [user_id]
        self.connections = {}  # user_id : WebSocket
        # {player1_id, player2_id, state: {"turn": player1, "board":  {"board": [[None]*3 for _ in range(3)]}}
        self.games = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        self.connections[user_id] = websocket

    def disconnect(self, user_id: int):
        del self.connections[user_id]

    async def join_queue(self, session: Session, user_id: int):

        if len(self.queue) > 0:
            waiting_user_id = self.queue.popleft()
            await self.start_game(session, user_id, waiting_user_id)
        else:
            self.queue.append(user_id)

        print(f"Queue: {self.queue}")
        print(f"Connections: {self.connections}")

    async def send_message(self, user_id: int, message: dict):
        await self.connections[user_id].send_json(message)

    def is_game_over(self, game_id: str, player_id: int):
        """
        Helper function for `handle_game_end` function

        Check if the game is over.
        Returns: 1 if player won, 2 if draw, 0 if game continues
        """
        game = self.games[game_id]
        board = game["state"]["board"]

        # Check rows and columns
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == player_id:  # Row i
                return 1
            if board[0][i] == board[1][i] == board[2][i] == player_id:  # Column i
                return 1

        # Check diagonals
        if board[0][0] == board[1][1] == board[2][2] == player_id:  # Main diagonal
            return 1
        if board[0][2] == board[1][1] == board[2][0] == player_id:  # Anti-diagonal
            return 1

        # Check for draw (all cells filled)
        if all(cell is not None for row in board for cell in row):
            return 2

        return 0

    async def handle_game_end(self, session: Session, game_id: str, current_player_id: int, opponent_player_id: int):
        is_game_over = self.is_game_over(
            game_id=game_id, player_id=current_player_id)
        if is_game_over == 0:
            return

        game_end_msg = {
            "type": GameMessageType.GAME_END.value,
            "game_id": game_id,
            "winner_id": current_player_id if is_game_over == 1 else None,
        }

        await self.send_message(current_player_id, game_end_msg)
        await self.send_message(opponent_player_id, game_end_msg)

        winner_id = current_player_id if is_game_over == 1 else None
        loser_id = opponent_player_id if is_game_over == 1 else None
        if winner_id and loser_id:
            winner = session.query(User).filter(User.id == winner_id).first()
            loser = session.query(User).filter(User.id == loser_id).first()
            winner.wins += 1
            loser.losses += 1
        else:
            # It's a draw - update both players
            player1 = session.query(User).filter(
                User.id == current_player_id).first()
            player2 = session.query(User).filter(
                User.id == opponent_player_id).first()
            player1.draws += 1
            player2.draws += 1
        session.commit()
        # Need to save the game state in the DB
        game = self.games[game_id]
        curr_game = session.query(Game).filter(Game.id == game_id).first()
        curr_game.status = GameStatus.COMPLETED
        curr_game.winner_id = winner_id
        curr_game.loser_id = loser_id
        curr_game.is_draw = is_game_over == 2
        curr_game.player1_move_count = game["state"]["player1_move_count"]
        curr_game.player2_move_count = game["state"]["player2_move_count"]
        curr_game.final_state = json.dumps(game["state"]["board"])
        session.commit()

        del self.games[game_id]

    async def start_game(self, session: Session, user_id1: int, user_id2: int):
        new_game = Game(
            player1_id=user_id1,
            player2_id=user_id2,
            status=GameStatus.IN_PROGRESS,
            final_state=None,
            is_draw=False,
            winner_id=None,
            loser_id=None,
            player1_move_count=0,
            player2_move_count=0
        )

        player1 = session.query(User).filter(User.id == user_id1).first()
        player2 = session.query(User).filter(User.id == user_id2).first()
        session.add(new_game)
        session.commit()

        self.games[new_game.id] = {
            "player1": user_id1,
            "player2": user_id2,
            "state": {
                "player1_move_count": 0,
                "player2_move_count": 0,
                "turn": user_id1,
                "board": [[None] * 3 for _ in range(3)]
            }
        }

        game_start_msg = {
            "type": GameMessageType.GAME_START.value,
            "game_id": new_game.id,
            "player1": {
                "id": user_id1,
                "username": player1.username,
            },
            "player2": {
                "id": user_id2,
                "username": player2.username,
            },
            "turn": user_id1  # if random.randint(0, 1) == 0 else user_id2
        }

        print(f"Game start message: {game_start_msg}")

        await self.send_message(user_id1, game_start_msg)
        await self.send_message(user_id2, game_start_msg)

    async def play_move(self, session: Session, game_id: str, current_player_id: int, row: int, col: int):
        game = self.games[game_id]
        print(f"Game: {game}")
        other_player_id = game["player2"] if current_player_id == game["player1"] else game["player1"]
        if game["state"]["turn"] != current_player_id:
            print("error 1")
            return

        if game["state"]["board"][row][col] is not None:
            print("error 2")
            return

        game["state"]["board"][row][col] = current_player_id
        game["state"]["turn"] = other_player_id
        game["state"][f"player{1 if current_player_id == game['player1'] else 2}_move_count"] += 1

        print(f"Game after move: {game}")
        # This needs to be a message sent from the Frontend client! Not constructed on the backend!

        game_move_msg = {
            "type": GameMessageType.GAME_MOVE.value,
            "game_id": game_id,
            "player_id": current_player_id,
            "turn": other_player_id,
            "row": row,
            "col": col,
        }
        await self.send_message(current_player_id, game_move_msg)
        await self.send_message(other_player_id, game_move_msg)

        await self.handle_game_end(session, game_id, current_player_id, other_player_id)


def create_websocket_token(user: User, redis_client: redis.Redis):
    websocket_token = str(uuid.uuid4())

    # Store mapping in Redis with short TTL (5 minutes)
    redis_client.setex(
        f"ws_token:{websocket_token}",
        300,  # 5 minute expiration
        json.dumps({"user_id": user.id,
                   "username": user.username})
    )

    return websocket_token


def get_current_user_from_websocket_token(token: str, session: Session, redis_client: redis.Redis):
    data = redis_client.get(f"ws_token:{token}")
    if not data:
        print(f"No data found for token: {token}")
        raise ValueError("Invalid token")
    data = json.loads(data)

    user_id = data["user_id"]
    user = session.query(User).filter(User.id == user_id).first()
    print(f"User in function is: {user}")
    if not user:
        print(f"User not found for id: {user_id}")
        raise ValueError("User not found")
    return user


def leaderboard(session: Session):
    '''
    - Leaderboard: return top 3 users by win count or **efficiency**
    - *Efficiency = average number of moves per win (lower is better)*
    '''
    leaderboard = session.query(
        User.id,
        User.username,
        User.wins,
        User.losses,
        User.draws
    ).filter(
        User.wins + User.losses + User.draws >= LEADERBOARD_MIN_GAMES
    ).order_by(
        User.wins.desc()
    ).limit(3).subquery()

    print(f"Leaderboard: {session.query(leaderboard).all()}")

    efficiency = session.query(
        leaderboard.c.id.label("user_id"),
        leaderboard.c.username,
        leaderboard.c.wins,
        leaderboard.c.losses,
        leaderboard.c.draws,
        case(
            (leaderboard.c.wins == 0, None),
            else_=func.avg(Game.player1_move_count)
        ).label("efficiency")
    ).outerjoin(
        Game,
        Game.winner_id == leaderboard.c.id
    ).group_by(
        leaderboard.c.id,
        leaderboard.c.username,
        leaderboard.c.wins,
        leaderboard.c.losses,
        leaderboard.c.draws
    ).order_by(
        leaderboard.c.wins.desc(),
        case(
            (leaderboard.c.wins == 0, 999),  # Put users with 0 wins at the end
            else_=func.avg(Game.player1_move_count)
        ).asc()
    ).all()

    # Convert to dictionaries and handle Decimal conversion
    result = []
    for row in efficiency:
        row_dict = dict(row._mapping)
        # Convert efficiency to float if it's not None, otherwise keep None
        if row_dict['efficiency'] is not None:
            row_dict['efficiency'] = float(row_dict['efficiency'])
        result.append(row_dict)

    return result
