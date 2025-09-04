"""
Tests for game services
"""

import pytest
import json
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from collections import deque

from routes.game.services import (
    GameManager, create_websocket_token, get_current_user_from_websocket_token,
    leaderboard, get_redis_client, LEADERBOARD_MIN_GAMES
)
from routes.game.schemas import GameMessageType
from models.game import Game, GameStatus
from tests.create_resources import (
    create_test_user, create_test_game, create_completed_game,
    create_leaderboard_test_data, cleanup_test_data
)


class TestGameManager:
    """Test cases for GameManager class"""

    @pytest.fixture
    def game_manager(self):
        """Create a fresh GameManager instance for each test"""
        return GameManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing"""
        websocket = MagicMock()
        websocket.send_json = AsyncMock()
        return websocket

    @pytest.mark.asyncio
    async def test_connect(self, game_manager, mock_websocket):
        """Test WebSocket connection management"""
        user_id = 123

        await game_manager.connect(user_id, mock_websocket)

        assert user_id in game_manager.connections
        assert game_manager.connections[user_id] == mock_websocket

    def test_disconnect(self, game_manager, mock_websocket):
        """Test WebSocket disconnection"""
        user_id = 123
        game_manager.connections[user_id] = mock_websocket

        game_manager.disconnect(user_id)

        assert user_id not in game_manager.connections

    @pytest.mark.asyncio
    async def test_join_queue_first_player(self, game_manager, db_session):
        """Test joining queue as first player"""
        user_id = 123

        await game_manager.join_queue(db_session, user_id)

        assert user_id in game_manager.queue
        assert len(game_manager.queue) == 1

    @patch.object(GameManager, 'start_game')
    @pytest.mark.asyncio
    async def test_join_queue_second_player(self, mock_start_game, game_manager, db_session):
        """Test joining queue as second player triggers game start"""
        user1_id = 123
        user2_id = 456

        # Add first player to queue
        game_manager.queue.append(user1_id)

        # Mock start_game to be async
        mock_start_game.return_value = None

        await game_manager.join_queue(db_session, user2_id)

        # Queue should be empty after matching
        assert len(game_manager.queue) == 0
        # start_game should have been called
        mock_start_game.assert_called_once_with(db_session, user2_id, user1_id)

    @pytest.mark.asyncio
    async def test_send_message(self, game_manager, mock_websocket):
        """Test sending message to WebSocket"""
        user_id = 123
        message = {"type": "test", "data": "hello"}

        game_manager.connections[user_id] = mock_websocket

        await game_manager.send_message(user_id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    def test_is_game_over_win_row(self, game_manager):
        """Test game over detection for row win"""
        game_id = "test_game"
        player_id = 123

        # Create game with winning row
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [player_id, player_id, player_id],  # Winning row
                    [None, None, None],
                    [None, None, None]
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 1  # Player won

    def test_is_game_over_win_column(self, game_manager):
        """Test game over detection for column win"""
        game_id = "test_game"
        player_id = 123

        # Create game with winning column
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [player_id, None, None],
                    [player_id, None, None],
                    [player_id, None, None]  # Winning column
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 1  # Player won

    def test_is_game_over_win_diagonal(self, game_manager):
        """Test game over detection for diagonal win"""
        game_id = "test_game"
        player_id = 123

        # Create game with winning diagonal
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [player_id, None, None],
                    [None, player_id, None],
                    [None, None, player_id]  # Winning diagonal
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 1  # Player won

    def test_is_game_over_win_anti_diagonal(self, game_manager):
        """Test game over detection for anti-diagonal win"""
        game_id = "test_game"
        player_id = 123

        # Create game with winning anti-diagonal
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [None, None, player_id],
                    [None, player_id, None],
                    [player_id, None, None]  # Winning anti-diagonal
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 1  # Player won

    def test_is_game_over_draw(self, game_manager):
        """Test game over detection for draw"""
        game_id = "test_game"
        player_id = 123
        opponent_id = 456

        # Create full board with no winner
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [player_id, opponent_id, player_id],
                    [opponent_id, player_id, opponent_id],
                    [opponent_id, player_id, opponent_id]
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 2  # Draw

    def test_is_game_over_continue(self, game_manager):
        """Test game continues when no win/draw condition"""
        game_id = "test_game"
        player_id = 123

        # Create game in progress
        game_manager.games[game_id] = {
            "state": {
                "board": [
                    [player_id, None, None],
                    [None, None, None],
                    [None, None, None]
                ]
            }
        }

        result = game_manager.is_game_over(game_id, player_id)
        assert result == 0  # Game continues

    @patch.object(GameManager, 'send_message')
    @patch.object(GameManager, 'is_game_over')
    @pytest.mark.asyncio
    async def test_handle_game_end_no_game_over(self, mock_is_game_over, mock_send_message, game_manager, db_session):
        """Test handle_game_end when game is not over"""
        mock_is_game_over.return_value = 0  # Game continues

        await game_manager.handle_game_end(db_session, "game_id", 123, 456)

        # Should return early, no messages sent
        mock_send_message.assert_not_called()

    @patch.object(GameManager, 'send_message')
    @patch.object(GameManager, 'is_game_over')
    @pytest.mark.asyncio
    async def test_handle_game_end_player_wins(self, mock_is_game_over, mock_send_message, game_manager, db_session):
        """Test handle_game_end when player wins"""
        # Create test users and game
        player1 = create_test_user(db_session, username="player1")
        player2 = create_test_user(db_session, username="player2")
        game = create_test_game(db_session, player1=player1, player2=player2)

        game_manager.games[game.id] = {
            "state": {
                "player1_move_count": 3,
                "player2_move_count": 2,
                "board": [[None] * 3 for _ in range(3)]
            }
        }

        mock_is_game_over.return_value = 1  # Player wins
        mock_send_message.return_value = None

        await game_manager.handle_game_end(db_session, game.id, player1.id, player2.id)

        # Verify messages were sent
        assert mock_send_message.call_count == 2

        # Verify database updates
        db_session.refresh(player1)
        db_session.refresh(player2)
        assert player1.wins == 1
        assert player2.losses == 1

        # Verify game was removed from memory
        assert game.id not in game_manager.games

        cleanup_test_data(db_session)

    @patch.object(GameManager, 'send_message')
    @patch.object(GameManager, 'is_game_over')
    @pytest.mark.asyncio
    async def test_handle_game_end_draw(self, mock_is_game_over, mock_send_message, game_manager, db_session):
        """Test handle_game_end when game is a draw"""
        # Create test users and game
        player1 = create_test_user(db_session, username="player1")
        player2 = create_test_user(db_session, username="player2")
        game = create_test_game(db_session, player1=player1, player2=player2)

        game_manager.games[game.id] = {
            "state": {
                "player1_move_count": 5,
                "player2_move_count": 4,
                "board": [[None] * 3 for _ in range(3)]
            }
        }

        mock_is_game_over.return_value = 2  # Draw
        mock_send_message.return_value = None

        await game_manager.handle_game_end(db_session, game.id, player1.id, player2.id)

        # Verify database updates
        db_session.refresh(player1)
        db_session.refresh(player2)
        assert player1.draws == 1
        assert player2.draws == 1

        cleanup_test_data(db_session)

    @patch.object(GameManager, 'send_message')
    @pytest.mark.asyncio
    async def test_start_game(self, mock_send_message, game_manager, db_session):
        """Test game start functionality"""
        # Create test users
        player1 = create_test_user(db_session, username="player1")
        player2 = create_test_user(db_session, username="player2")

        mock_send_message.return_value = None

        await game_manager.start_game(db_session, player1.id, player2.id)

        # Verify game was created in database
        game = db_session.query(Game).filter(
            Game.player1_id == player1.id,
            Game.player2_id == player2.id
        ).first()
        assert game is not None
        assert game.status == GameStatus.IN_PROGRESS

        # Verify game was added to memory
        assert game.id in game_manager.games
        game_state = game_manager.games[game.id]
        assert game_state["player1"] == player1.id
        assert game_state["player2"] == player2.id
        assert game_state["state"]["turn"] == player1.id

        # Verify messages were sent
        assert mock_send_message.call_count == 2

        cleanup_test_data(db_session)

    @patch.object(GameManager, 'send_message')
    @patch.object(GameManager, 'handle_game_end')
    @pytest.mark.asyncio
    async def test_play_move_success(self, mock_handle_game_end, mock_send_message, game_manager, db_session):
        """Test successful move play"""
        # Create test users
        player1 = create_test_user(db_session, username="player1")
        player2 = create_test_user(db_session, username="player2")

        # Set up game state
        game_id = "test_game"
        game_manager.games[game_id] = {
            "player1": player1.id,
            "player2": player2.id,
            "state": {
                "turn": player1.id,
                "board": [[None] * 3 for _ in range(3)],
                "player1_move_count": 0,
                "player2_move_count": 0
            }
        }

        mock_send_message.return_value = None
        mock_handle_game_end.return_value = None

        await game_manager.play_move(db_session, game_id, player1.id, 0, 0)

        # Verify board was updated
        board = game_manager.games[game_id]["state"]["board"]
        assert board[0][0] == player1.id

        # Verify turn was switched
        assert game_manager.games[game_id]["state"]["turn"] == player2.id

        # Verify move count was incremented
        assert game_manager.games[game_id]["state"]["player1_move_count"] == 1

        # Verify messages were sent
        assert mock_send_message.call_count == 2

        # Verify game end check was called
        mock_handle_game_end.assert_called_once()

    @pytest.mark.asyncio
    async def test_play_move_wrong_turn(self, game_manager, db_session):
        """Test play move when it's not player's turn"""
        player1_id = 123
        player2_id = 456

        # Set up game state with player2's turn
        game_id = "test_game"
        game_manager.games[game_id] = {
            "player1": player1_id,
            "player2": player2_id,
            "state": {
                "turn": player2_id,  # Player2's turn
                "board": [[None] * 3 for _ in range(3)]
            }
        }

        # Try to play move as player1 (wrong turn)
        await game_manager.play_move(db_session, game_id, player1_id, 0, 0)

        # Board should remain unchanged
        board = game_manager.games[game_id]["state"]["board"]
        assert board[0][0] is None

    @pytest.mark.asyncio
    async def test_play_move_occupied_cell(self, game_manager, db_session):
        """Test play move on occupied cell"""
        player1_id = 123
        player2_id = 456

        # Set up game state with occupied cell
        game_id = "test_game"
        game_manager.games[game_id] = {
            "player1": player1_id,
            "player2": player2_id,
            "state": {
                "turn": player1_id,
                "board": [
                    [player2_id, None, None],  # Cell [0,0] already occupied
                    [None, None, None],
                    [None, None, None]
                ]
            }
        }

        # Try to play move on occupied cell
        await game_manager.play_move(db_session, game_id, player1_id, 0, 0)

        # Board should remain unchanged
        board = game_manager.games[game_id]["state"]["board"]
        assert board[0][0] == player2_id  # Still player2


class TestGameServiceFunctions:
    """Test cases for standalone game service functions"""

    def test_create_websocket_token(self, db_session, mock_redis):
        """Test WebSocket token creation"""
        user = create_test_user(db_session, username="wsuser")

        token = create_websocket_token(user, mock_redis)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token was stored in Redis
        stored_data = mock_redis.get(f"ws_token:{token}")
        assert stored_data is not None

        # Verify stored data
        data = json.loads(stored_data)
        assert data["user_id"] == user.id
        assert data["username"] == user.username

        cleanup_test_data(db_session)

    def test_get_current_user_from_websocket_token_success(self, db_session, mock_redis):
        """Test successful user retrieval from WebSocket token"""
        user = create_test_user(db_session, username="wsuser")

        # Store token data in mock Redis
        token = "test_token"
        token_data = json.dumps(
            {"user_id": user.id, "username": user.username})
        mock_redis.setex(f"ws_token:{token}", 300, token_data)

        result = get_current_user_from_websocket_token(
            token, db_session, mock_redis)

        assert result.id == user.id
        assert result.username == user.username

        cleanup_test_data(db_session)

    def test_get_current_user_from_websocket_token_invalid_token(self, db_session, mock_redis):
        """Test user retrieval with invalid WebSocket token"""
        with pytest.raises(ValueError, match="Invalid token"):
            get_current_user_from_websocket_token(
                "invalid_token", db_session, mock_redis)

    def test_get_current_user_from_websocket_token_user_not_found(self, db_session, mock_redis):
        """Test user retrieval when user doesn't exist"""
        # Store token data for non-existent user
        token = "test_token"
        token_data = json.dumps({"user_id": 999, "username": "nonexistent"})
        mock_redis.setex(f"ws_token:{token}", 300, token_data)

        with pytest.raises(ValueError, match="User not found"):
            get_current_user_from_websocket_token(
                token, db_session, mock_redis)

    def test_leaderboard_success(self, db_session):
        """Test successful leaderboard generation"""
        users = create_leaderboard_test_data(db_session)

        result = leaderboard(db_session)

        assert isinstance(result, list)
        # Should only include users with sufficient games
        valid_users = [u for u in users if (
            u.wins + u.losses + u.draws) >= LEADERBOARD_MIN_GAMES]
        assert len(result) <= len(valid_users)

        # Verify structure
        for entry in result:
            assert "user_id" in entry
            assert "username" in entry
            assert "wins" in entry
            assert "losses" in entry
            assert "draws" in entry
            # efficiency can be None

        # Verify ordering (by wins desc)
        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i]["wins"] >= result[i + 1]["wins"]

        cleanup_test_data(db_session)

    def test_leaderboard_empty(self, db_session):
        """Test leaderboard with no qualifying users"""
        # Create users with insufficient games
        create_test_user(db_session, wins=1, losses=1, draws=0)  # Only 2 games

        result = leaderboard(db_session)

        assert isinstance(result, list)
        assert len(result) == 0

        cleanup_test_data(db_session)

    def test_leaderboard_efficiency_calculation(self, db_session):
        """Test leaderboard efficiency calculation"""
        # Create user with wins
        user = create_test_user(
            db_session, username="efficient", wins=3, losses=1, draws=1)

        # Create games for efficiency calculation
        for i in range(3):
            create_completed_game(
                db_session,
                player1=user,
                winner=user,
                player1_moves=3 + i,  # Different move counts for average
                player2_moves=2
            )

        result = leaderboard(db_session)

        assert len(result) == 1
        entry = result[0]
        assert entry["user_id"] == user.id
        assert entry["efficiency"] is not None
        assert isinstance(entry["efficiency"], float)

        cleanup_test_data(db_session)

    def test_leaderboard_no_efficiency_for_zero_wins(self, db_session):
        """Test leaderboard efficiency for users with zero wins"""
        # Create user with no wins but enough games
        user = create_test_user(
            db_session, username="loser", wins=0, losses=3, draws=0)

        result = leaderboard(db_session)

        assert len(result) == 1
        entry = result[0]
        assert entry["user_id"] == user.id
        assert entry["efficiency"] is None  # No efficiency for 0 wins

        cleanup_test_data(db_session)

    def test_get_redis_client(self):
        """Test Redis client creation"""
        with patch('redis.Redis') as mock_redis_class:
            mock_redis_instance = MagicMock()
            mock_redis_class.return_value = mock_redis_instance

            client = get_redis_client()

            mock_redis_class.assert_called_once_with(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            assert client == mock_redis_instance
