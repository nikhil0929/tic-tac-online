"""
Tests for user controller endpoints
"""

import pytest
from fastapi import status
from unittest.mock import patch, MagicMock

from tests.create_resources import create_test_user, cleanup_test_data
from routes.user.services import create_access_token


class TestUserController:
    """Test cases for user controller endpoints"""

    def test_get_current_user_success(self, client, db_session):
        """Test successful retrieval of current user"""
        # Create test user
        user = create_test_user(db_session, username="testuser123")

        # Create access token
        token = create_access_token({"username": user.username, "id": user.id})

        # Make request with token
        response = client.get(
            "/user/",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == user.username
        assert data["first_name"] == user.first_name
        assert data["last_name"] == user.last_name

        cleanup_test_data(db_session)

    def test_get_current_user_invalid_token(self, client):
        """Test get current user with invalid token"""
        response = client.get(
            "/user/",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in response.json()["detail"]

    def test_get_current_user_no_token(self, client):
        """Test get current user without token"""
        response = client.get("/user/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_user_success(self, client, db_session):
        """Test successful user creation"""
        user_data = {
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe123",
            "password": "securepassword"
        }

        response = client.post("/user/create", json=user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "id" in data

        # Verify user was created in database
        from models.user import User
        user = db_session.query(User).filter(
            User.username == "johndoe123").first()
        assert user is not None
        assert user.first_name == "John"
        assert user.last_name == "Doe"

        cleanup_test_data(db_session)

    def test_create_user_duplicate_username(self, client, db_session):
        """Test user creation with duplicate username"""
        # Create existing user
        create_test_user(db_session, username="existinguser")

        user_data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "username": "existinguser",
            "password": "password123"
        }

        response = client.post("/user/create", json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already exists" in response.json()["detail"]

        cleanup_test_data(db_session)

    def test_create_user_invalid_data(self, client):
        """Test user creation with invalid data"""
        user_data = {
            "first_name": "",  # Empty first name
            "username": "testuser",
            "password": "password123"
            # Missing last_name
        }

        response = client.post("/user/create", json=user_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_success(self, client, db_session):
        """Test successful user login"""
        # Create test user
        user = create_test_user(
            db_session, username="loginuser", password="testpass")

        login_data = {
            "username": "loginuser",
            "password": "testpass"
        }

        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["id"] == user.id

        cleanup_test_data(db_session)

    def test_login_invalid_username(self, client, db_session):
        """Test login with invalid username"""
        login_data = {
            "username": "nonexistentuser",
            "password": "password123"
        }

        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_invalid_password(self, client, db_session):
        """Test login with invalid password"""
        # Create test user
        create_test_user(db_session, username="testuser",
                         password="correctpass")

        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

        cleanup_test_data(db_session)

    def test_login_invalid_data(self, client):
        """Test login with invalid request data"""
        login_data = {
            "username": "",  # Empty username
            # Missing password
        }

        response = client.post("/user/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('routes.user.controller.logger')
    def test_logging_in_endpoints(self, mock_logger, client, db_session):
        """Test that logging works correctly in endpoints"""
        # Test create user logging
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "username": "testlogger",
            "password": "password123"
        }

        client.post("/user/create", json=user_data)

        # Verify logging calls
        mock_logger.info.assert_called()

        # Test login logging
        login_data = {
            "username": "testlogger",
            "password": "password123"
        }

        client.post("/user/login", json=login_data)

        # Verify more logging calls
        assert mock_logger.info.call_count >= 2

        cleanup_test_data(db_session)
