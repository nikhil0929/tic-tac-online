#!/usr/bin/env python3
"""
Database cleanup script for tic-tac-toe simulation

This script cleans up all games and users from the database before running simulations.
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Add the project root to Python path so we can import our models
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from db import db, Session
    from models.user import User
    from models.game import Game
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def cleanup_database():
    """Clean up all games and users from the database"""
    print("Starting database cleanup...")

    try:
        # Get a database session
        session = next(db())

        # Delete all games first (due to foreign key constraints)
        games_deleted = session.query(Game).delete()
        print(f"Deleted {games_deleted} games")

        # Delete all users
        users_deleted = session.query(User).delete()
        print(f"Deleted {users_deleted} users")

        # Commit the changes
        session.commit()
        session.close()

        print("✅ Database cleanup completed successfully")
        return True

    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


def reset_sequences():
    """Reset auto-increment sequences for clean IDs"""
    print("Resetting ID sequences...")

    try:
        # Get database URL from environment or use default
        from dotenv import load_dotenv
        load_dotenv()

        db_url = os.getenv(
            "DATABASE_URL", "postgresql://username:password@localhost/tic_tac_toe")

        # Create engine for raw SQL execution
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Reset sequences to start from 1
            conn.execute(text("ALTER SEQUENCE user_id_seq RESTART WITH 1"))
            conn.execute(text("ALTER SEQUENCE game_id_seq RESTART WITH 1"))
            conn.commit()

        print("✅ ID sequences reset successfully")
        return True

    except Exception as e:
        print(f"Note: Could not reset sequences: {e}")
        print("This is not critical - simulation will still work")
        return False


def main():
    """Main cleanup function"""
    print("Tic-Tac-Toe Database Cleanup")
    print("=" * 40)

    # Clean up the database
    if cleanup_database():
        # Try to reset sequences for clean IDs
        reset_sequences()
        print("\n🎉 Database is now clean and ready for simulation!")
    else:
        print("\n⚠️  Cleanup failed. Check database connection and permissions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
