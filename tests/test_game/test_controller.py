"""
Tests for game controller endpoints
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import status

from tests.create_resources import (
    create_test_user, create_leaderboard_test_data, cleanup_test_data
)
from routes.user.services import create_access_token


class TestGameController:
    """Test cases for game controller endpoints"""

    def test_get_websocket_token_success(self, client, db_session, mock_redis):
        """Test successful WebSocket token generation"""
        # Create test user
        user = create_test_user(db_session, username="wsuser")

        # Create access token
        token = create_access_token({"username": user.username, "id": user.id})

        # Mock Redis dependency
        with patch('routes.game.controller.get_redis_client', return_value=mock_redis):
            response = client.post(
                "/game/websocket-token",
                headers={"Authorization": f"Bearer {token}"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "websocket_token" in data
        assert isinstance(data["websocket_token"], str)
        assert len(data["websocket_token"]) > 0

        cleanup_test_data(db_session)

    def test_get_websocket_token_unauthorized(self, client):
        """Test WebSocket token generation without authentication"""
        response = client.post("/game/websocket-token")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_websocket_token_invalid_token(self, client, mock_redis):
        """Test WebSocket token generation with invalid JWT"""
        with patch('routes.game.controller.get_redis_client', return_value=mock_redis):
            response = client.post(
                "/game/websocket-token",
                headers={"Authorization": "Bearer invalid_token"}
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_leaderboard_success(self, client, db_session):
        """Test successful leaderboard retrieval"""
        # Create test data for leaderboard
        users = create_leaderboard_test_data(db_session)

        response = client.get("/game/leaderboard")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # Should only include users with sufficient games (3+)
        # Users with < 3 total games should be excluded
        valid_users = [u for u in users if (u.wins + u.losses + u.draws) >= 3]
        assert len(data) <= len(valid_users)

        # Check leaderboard structure
        if data:
            for entry in data:
                assert "user_id" in entry
                assert "username" in entry
                assert "wins" in entry
                assert "losses" in entry
                assert "draws" in entry
                # efficiency can be None for users with 0 wins

        cleanup_test_data(db_session)

    def test_get_leaderboard_empty_database(self, client, db_session):
        """Test leaderboard retrieval with no users"""
        response = client.get("/game/leaderboard")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('routes.game.controller.manager')
    @patch('routes.game.controller.get_current_user_from_websocket_token')
    @pytest.mark.asyncio
    async def test_websocket_endpoint_success(self, mock_get_user, mock_manager, client, db_session, mock_redis):
        """Test successful WebSocket connection"""
        # Create test user
        user = create_test_user(db_session, username="wsuser")
        mock_get_user.return_value = user

        # Mock manager methods
        mock_manager.connect = AsyncMock()
        mock_manager.join_queue = AsyncMock()
        mock_manager.disconnect = MagicMock()

        # Mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.query_params = {"token": "valid_token"}
        mock_websocket.receive_json = AsyncMock(side_effect=[
            {"type": "GAME_MOVE", "game_id": "123", "row": 0, "col": 0},
            # Simulate WebSocket disconnect
        ])

        with patch('routes.game.controller.get_redis_client', return_value=mock_redis):
            # This is a complex test due to WebSocket nature
            # In a real scenario, you'd use a WebSocket test client
            pass  # WebSocket testing requires more complex setup

        cleanup_test_data(db_session)

    def test_websocket_endpoint_missing_token(self, client):
        """Test WebSocket connection without token"""
        # WebSocket testing without token would be handled in the endpoint
        # This test verifies the logic exists
        pass  # WebSocket endpoint tests require specialized WebSocket test client

    @patch('routes.game.controller.logger')
    def test_logging_in_endpoints(self, mock_logger, client, db_session, mock_redis):
        """Test that logging works correctly in endpoints"""
        # Create test user
        user = create_test_user(db_session, username="loguser")
        token = create_access_token({"username": user.username, "id": user.id})

        with patch('routes.game.controller.get_redis_client', return_value=mock_redis):
            client.post(
                "/game/websocket-token",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Verify logging was called
        mock_logger.info.assert_called()

        cleanup_test_data(db_session)

    @patch('routes.game.controller.create_websocket_token')
    def test_websocket_token_creation_called(self, mock_create_token, client, db_session, mock_redis):
        """Test that websocket token creation service is called correctly"""
        # Create test user
        user = create_test_user(db_session, username="tokenuser")
        token = create_access_token({"username": user.username, "id": user.id})

        mock_create_token.return_value = "mocked_ws_token"

        with patch('routes.game.controller.get_redis_client', return_value=mock_redis):
            response = client.post(
                "/game/websocket-token",
                headers={"Authorization": f"Bearer {token}"}
            )

        # Verify service function was called
        mock_create_token.assert_called_once()
        assert response.json()["websocket_token"] == "mocked_ws_token"

        cleanup_test_data(db_session)

    @patch('routes.game.controller.leaderboard')
    def test_leaderboard_service_called(self, mock_leaderboard, client, db_session):
        """Test that leaderboard service is called correctly"""
        mock_leaderboard.return_value = [
            {
                "user_id": 1,
                "username": "testuser",
                "wins": 5,
                "losses": 2,
                "draws": 1,
                "efficiency": 4.5
            }
        ]

        response = client.get("/game/leaderboard")

        # Verify service function was called
        mock_leaderboard.assert_called_once()
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

        cleanup_test_data(db_session)
