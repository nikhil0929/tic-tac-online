"""
Tests for user services
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from routes.user.services import (
    create_user, login, get_current_user, create_access_token,
    verify_password, get_password_hash, authenticate_user
)
from routes.user.schemas import Token, TokenData
from tests.create_resources import create_test_user, cleanup_test_data


class TestUserServices:
    """Test cases for user service functions"""

    def test_create_user_success(self, db_session):
        """Test successful user creation"""
        result = create_user(
            session=db_session,
            first_name="John",
            last_name="Doe",
            username="johndoe",
            password="securepass123"
        )

        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert result.id is not None

        # Verify user in database
        from models.user import User
        user = db_session.query(User).filter(
            User.username == "johndoe").first()
        assert user is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.username == "johndoe"
        assert user.password != "securepass123"  # Should be hashed

        cleanup_test_data(db_session)

    def test_create_user_duplicate_username(self, db_session):
        """Test user creation with existing username"""
        # Create existing user
        create_test_user(db_session, username="existinguser")

        with pytest.raises(HTTPException) as exc_info:
            create_user(
                session=db_session,
                first_name="Jane",
                last_name="Doe",
                username="existinguser",
                password="password123"
            )

        assert exc_info.value.status_code == 400
        assert "username already exists" in str(exc_info.value.detail)

        cleanup_test_data(db_session)

    def test_login_success(self, db_session):
        """Test successful login"""
        # Create test user
        user = create_test_user(
            db_session, username="testuser", password="testpass")

        result = login(
            session=db_session,
            username="testuser",
            password="testpass"
        )

        assert isinstance(result, Token)
        assert result.token_type == "bearer"
        assert result.access_token is not None
        assert result.id == user.id

        cleanup_test_data(db_session)

    def test_login_invalid_username(self, db_session):
        """Test login with non-existent username"""
        with pytest.raises(HTTPException) as exc_info:
            login(
                session=db_session,
                username="nonexistent",
                password="password123"
            )

        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)

    def test_login_invalid_password(self, db_session):
        """Test login with wrong password"""
        create_test_user(db_session, username="testuser",
                         password="correctpass")

        with pytest.raises(HTTPException) as exc_info:
            login(
                session=db_session,
                username="testuser",
                password="wrongpass"
            )

        assert exc_info.value.status_code == 401
        assert "Incorrect username or password" in str(exc_info.value.detail)

        cleanup_test_data(db_session)

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_get_current_user_success(self, db_session):
        """Test successful current user retrieval"""
        # Create test user
        user = create_test_user(db_session, username="testuser")

        # Create valid token
        token = create_access_token({"username": user.username, "id": user.id})

        result = get_current_user(session=db_session, token=token)

        assert result.id == user.id
        assert result.username == user.username

        cleanup_test_data(db_session)

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_get_current_user_invalid_token(self, db_session):
        """Test current user retrieval with invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(session=db_session, token="invalid_token")

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_get_current_user_token_missing_data(self, db_session):
        """Test current user retrieval with token missing username or id"""
        # Create token with missing username
        incomplete_token = jwt.encode(
            {"id": 123, "exp": datetime.now(
                timezone.utc) + timedelta(minutes=15)},
            "test_secret",
            algorithm="HS256"
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(session=db_session, token=incomplete_token)

        assert exc_info.value.status_code == 401

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_get_current_user_user_not_found(self, db_session):
        """Test current user retrieval when user doesn't exist in DB"""
        # Create token for non-existent user
        token = create_access_token({"username": "nonexistent", "id": 999})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(session=db_session, token=token)

        assert exc_info.value.status_code == 401

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_create_access_token_with_expiry(self):
        """Test access token creation with custom expiry"""
        data = {"username": "testuser", "id": 123}
        expires_delta = timedelta(minutes=30)

        token = create_access_token(data, expires_delta)

        # Decode and verify token
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])
        assert payload["username"] == "testuser"
        assert payload["id"] == 123
        assert "exp" in payload

    @patch('routes.user.services.JWT_SECRET_KEY', 'test_secret')
    @patch('routes.user.services.ALGORITHM', 'HS256')
    def test_create_access_token_default_expiry(self):
        """Test access token creation with default expiry"""
        data = {"username": "testuser", "id": 123}

        token = create_access_token(data)

        # Decode and verify token
        payload = jwt.decode(token, "test_secret", algorithms=["HS256"])
        assert payload["username"] == "testuser"
        assert payload["id"] == 123

        # Check that expiry is set (default 15 minutes)
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = exp_time - now
        assert timedelta(minutes=14) < time_diff < timedelta(minutes=16)

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert hashed is not None
        assert len(hashed) > 0

        # Verify hash is consistent
        hashed2 = get_password_hash(password)
        assert hashed != hashed2  # Bcrypt uses salt, so hashes should differ

    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        user = create_test_user(
            db_session, username="authuser", password="authpass")

        result = authenticate_user(db_session, "authuser", "authpass")

        assert result is not False
        assert result.id == user.id
        assert result.username == user.username

        cleanup_test_data(db_session)

    def test_authenticate_user_wrong_username(self, db_session):
        """Test authentication with wrong username"""
        create_test_user(db_session, username="authuser", password="authpass")

        result = authenticate_user(db_session, "wronguser", "authpass")

        assert result is False

        cleanup_test_data(db_session)

    def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password"""
        create_test_user(db_session, username="authuser", password="authpass")

        result = authenticate_user(db_session, "authuser", "wrongpass")

        assert result is False

        cleanup_test_data(db_session)

    @patch('routes.user.services.logger')
    def test_logging_in_services(self, mock_logger, db_session):
        """Test that logging works correctly in services"""
        # Test create_user logging
        create_user(
            session=db_session,
            first_name="Log",
            last_name="Test",
            username="logtest",
            password="password123"
        )

        # Verify logging was called
        mock_logger.info.assert_called()

        cleanup_test_data(db_session)
