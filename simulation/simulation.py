#!/usr/bin/env python3
"""
Tic-Tac-Toe Game Simulation Script

This script simulates multiple concurrent games across multiple players with different strategies.
It validates game outcomes and provides statistics on player performance.
"""

import asyncio
import json
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict
import requests
import websockets
from websockets.exceptions import ConnectionClosedError


class PlayerStrategy(Enum):
    """Different AI strategies for players"""
    RANDOM = "random"
    SMART = "smart"
    DEFENSIVE = "defensive"
    AGGRESSIVE = "aggressive"
    BLOCKING = "blocking"


@dataclass
class GameResult:
    """Represents the result of a single game"""
    game_id: str
    player1_id: int
    player2_id: int
    winner_id: Optional[int]
    is_draw: bool
    moves: List[Tuple[int, int, int]]  # (player_id, row, col)
    duration: float
    player1_strategy: PlayerStrategy
    player2_strategy: PlayerStrategy


@dataclass
class PlayerStats:
    """Statistics for a single player"""
    player_id: int
    username: str
    strategy: PlayerStrategy
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    total_moves: int = 0
    avg_moves_per_game: float = 0.0
    win_ratio: float = 0.0
    games_played: List[str] = field(default_factory=list)


class TicTacToeBoard:
    """Local representation of the tic-tac-toe board for strategy calculations"""

    def __init__(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]

    def make_move(self, row: int, col: int, player_id: int) -> bool:
        """Make a move on the board"""
        if self.board[row][col] is None:
            self.board[row][col] = player_id
            return True
        return False

    def get_available_moves(self) -> List[Tuple[int, int]]:
        """Get all available moves"""
        moves = []
        for row in range(3):
            for col in range(3):
                if self.board[row][col] is None:
                    moves.append((row, col))
        return moves

    def check_winner(self) -> Optional[int]:
        """Check if there's a winner"""
        # Check rows
        for row in range(3):
            if self.board[row][0] == self.board[row][1] == self.board[row][2] and self.board[row][0] is not None:
                return self.board[row][0]

        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] is not None:
                return self.board[0][col]

        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] is not None:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] is not None:
            return self.board[0][2]

        return None

    def is_full(self) -> bool:
        """Check if board is full"""
        return all(self.board[row][col] is not None for row in range(3) for col in range(3))

    def get_winning_move(self, player_id: int) -> Optional[Tuple[int, int]]:
        """Find a winning move for the given player"""
        for row, col in self.get_available_moves():
            # Try the move
            self.board[row][col] = player_id
            if self.check_winner() == player_id:
                self.board[row][col] = None  # Undo
                return (row, col)
            self.board[row][col] = None  # Undo
        return None

    def get_blocking_move(self, player_id: int) -> Optional[Tuple[int, int]]:
        """Find a move that blocks the opponent from winning"""
        opponent_id = 3 - \
            player_id if player_id in [1, 2] else (2 if player_id == 1 else 1)
        return self.get_winning_move(opponent_id)


class GamePlayer:
    """Represents a player with a specific strategy"""

    def __init__(self, player_id: int, username: str, strategy: PlayerStrategy, token: str):
        self.player_id = player_id
        self.username = username
        self.strategy = strategy
        self.token = token
        self.websocket = None
        self.current_game_id = None
        self.board = TicTacToeBoard()
        self.is_my_turn = False
        self.opponent_id = None
        self.game_results_ref = None

    async def connect_websocket(self, base_url: str):
        """Connect to the WebSocket endpoint"""
        ws_url = f"{base_url.replace('http', 'ws')}/game/ws?token={self.token}"
        try:
            self.websocket = await websockets.connect(ws_url)
            print(f"Player {self.username} connected to WebSocket")
        except Exception as e:
            print(f"Failed to connect player {self.username}: {e}")
            raise

    async def listen_for_messages(self, game_results: Dict[str, GameResult]):
        """Listen for WebSocket messages and respond accordingly"""
        self.game_results_ref = game_results
        try:
            while True:
                message = await self.websocket.recv()
                data = json.loads(message)
                await self.handle_message(data, game_results)
        except ConnectionClosedError:
            print(f"WebSocket connection closed for player {self.username}")
        except Exception as e:
            print(f"Error in message listener for player {self.username}: {e}")

    async def handle_message(self, data: Dict, game_results: Dict[str, GameResult]):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")

        if message_type == "GAME_START":
            await self.handle_game_start(data, game_results)
        elif message_type == "GAME_MOVE":
            await self.handle_game_move(data)
        elif message_type == "GAME_END":
            await self.handle_game_end(data, game_results)

    async def handle_game_start(self, data: Dict, game_results: Dict[str, GameResult]):
        """Handle game start message"""
        self.current_game_id = data["game_id"]
        self.board = TicTacToeBoard()

        player1 = data["player1"]
        player2 = data["player2"]

        if player1["id"] == self.player_id:
            self.opponent_id = player2["id"]
        else:
            self.opponent_id = player1["id"]

        self.is_my_turn = (data["turn"] == self.player_id)

        # Initialize game result tracking
        if self.current_game_id not in game_results:
            game_results[self.current_game_id] = GameResult(
                game_id=self.current_game_id,
                player1_id=player1["id"],
                player2_id=player2["id"],
                winner_id=None,
                is_draw=False,
                moves=[],
                duration=0.0,
                player1_strategy=PlayerStrategy.RANDOM,  # Will be updated
                player2_strategy=PlayerStrategy.RANDOM   # Will be updated
            )

        print(
            f"Game {self.current_game_id} started: {self.username} vs opponent")

        if self.is_my_turn:
            await self.make_move()

    async def handle_game_move(self, data: Dict):
        """Handle game move message"""
        player_id = data["player_id"]
        row = data["row"]
        col = data["col"]

        # Update local board
        self.board.make_move(row, col, player_id)
        self.is_my_turn = (data["turn"] == self.player_id)

        # Track moves in game results
        if self.current_game_id and self.game_results_ref and self.current_game_id in self.game_results_ref:
            self.game_results_ref[self.current_game_id].moves.append(
                (player_id, row, col))

        print(
            f"Move made in game {self.current_game_id}: Player {player_id} -> ({row}, {col})")

        if self.is_my_turn:
            # Add some realistic delay
            await asyncio.sleep(random.uniform(0.1, 0.5))
            await self.make_move()

    async def handle_game_end(self, data: Dict, game_results: Dict[str, GameResult]):
        """Handle game end message"""
        game_id = data["game_id"]
        winner_id = data.get("winner_id")

        if game_id in game_results:
            game_results[game_id].winner_id = winner_id
            game_results[game_id].is_draw = (winner_id is None)

        result_str = f"Winner: {winner_id}" if winner_id else "DRAW"
        print(f"Game {game_id} ended. {result_str}")

        self.current_game_id = None
        self.opponent_id = None
        self.is_my_turn = False

    async def make_move(self):
        """Make a move based on the player's strategy"""
        if not self.current_game_id or not self.is_my_turn:
            return

        move = self.choose_move()
        if move:
            row, col = move
            message = {
                "type": "GAME_MOVE",
                "game_id": self.current_game_id,
                "row": row,
                "col": col
            }
            await self.websocket.send(json.dumps(message))

    def choose_move(self) -> Optional[Tuple[int, int]]:
        """Choose a move based on the player's strategy"""
        available_moves = self.board.get_available_moves()

        if not available_moves:
            return None

        if self.strategy == PlayerStrategy.RANDOM:
            return random.choice(available_moves)

        elif self.strategy == PlayerStrategy.SMART:
            # First, try to win
            winning_move = self.board.get_winning_move(self.player_id)
            if winning_move:
                return winning_move

            # Then, try to block opponent
            blocking_move = self.board.get_blocking_move(self.player_id)
            if blocking_move:
                return blocking_move

            # Take center if available
            if (1, 1) in available_moves:
                return (1, 1)

            # Take corners
            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            corner_moves = [
                move for move in corners if move in available_moves]
            if corner_moves:
                return random.choice(corner_moves)

            # Take any remaining move
            return random.choice(available_moves)

        elif self.strategy == PlayerStrategy.DEFENSIVE:
            # Always try to block first
            blocking_move = self.board.get_blocking_move(self.player_id)
            if blocking_move:
                return blocking_move

            # Then try to win
            winning_move = self.board.get_winning_move(self.player_id)
            if winning_move:
                return winning_move

            # Take center or corners
            if (1, 1) in available_moves:
                return (1, 1)

            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            corner_moves = [
                move for move in corners if move in available_moves]
            if corner_moves:
                return random.choice(corner_moves)

            return random.choice(available_moves)

        elif self.strategy == PlayerStrategy.AGGRESSIVE:
            # Always try to win first
            winning_move = self.board.get_winning_move(self.player_id)
            if winning_move:
                return winning_move

            # Take center aggressively
            if (1, 1) in available_moves:
                return (1, 1)

            # Take corners aggressively
            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            corner_moves = [
                move for move in corners if move in available_moves]
            if corner_moves:
                return random.choice(corner_moves)

            # Block only if no other good moves
            blocking_move = self.board.get_blocking_move(self.player_id)
            if blocking_move:
                return blocking_move

            return random.choice(available_moves)

        elif self.strategy == PlayerStrategy.BLOCKING:
            # Pure blocking strategy - always blocks, rarely tries to win
            blocking_move = self.board.get_blocking_move(self.player_id)
            if blocking_move:
                return blocking_move

            # Only try to win if no blocking needed
            winning_move = self.board.get_winning_move(self.player_id)
            if winning_move:
                return winning_move

            # Take center
            if (1, 1) in available_moves:
                return (1, 1)

            return random.choice(available_moves)

        return random.choice(available_moves)


class GameSimulator:
    """Main simulation orchestrator"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.players: List[GamePlayer] = []
        self.game_results: Dict[str, GameResult] = {}
        self.player_stats: Dict[int, PlayerStats] = {}

    def cleanup_database(self):
        """Clean up all existing games and users from the database"""
        print("Cleaning up existing data...")

        try:
            # Import database modules from parent directory
            import sys
            import os
            parent_dir = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, parent_dir)

            from db import db
            from models.user import User
            from models.game import Game

            # Get a database session
            session = next(db())

            # Delete all games first (due to foreign key constraints)
            games_deleted = session.query(Game).delete()
            print(f"Deleted {games_deleted} existing games")

            # Delete all users
            users_deleted = session.query(User).delete()
            print(f"Deleted {users_deleted} existing users")

            # Commit the changes
            session.commit()
            session.close()

            print("✅ Database cleanup completed successfully")
            return True

        except Exception as e:
            print(f"❌ Database cleanup failed: {e}")
            print("Proceeding with simulation anyway...")
            if 'session' in locals():
                try:
                    session.rollback()
                    session.close()
                except:
                    pass
            return False

    def create_unique_usernames(self, num_users: int) -> List[str]:
        """Create unique usernames with timestamp to avoid conflicts"""
        timestamp = int(time.time())
        return [f"sim_player_{i+1}_{timestamp}" for i in range(num_users)]

    def create_test_users(self, num_users: int) -> List[Dict]:
        """Create test users via API"""
        users = []
        strategies = list(PlayerStrategy)
        unique_usernames = self.create_unique_usernames(num_users)

        for i in range(num_users):
            username = unique_usernames[i]
            strategy = strategies[i % len(strategies)]

            user_data = {
                "first_name": f"SimPlayer",
                "last_name": f"{i+1}",
                "username": username,
                "password": "testpass123"
            }

            try:
                response = requests.post(
                    f"{self.base_url}/user/create", json=user_data)
                if response.status_code == 200:
                    result = response.json()
                    users.append({
                        "id": result["id"],
                        "username": username,
                        "token": result["access_token"],
                        "strategy": strategy
                    })
                    print(
                        f"Created user: {username} with strategy {strategy.value}")
                else:
                    print(f"Failed to create user {username}: {response.text}")
            except Exception as e:
                print(f"Error creating user {username}: {e}")

        return users

    async def setup_players(self, users: List[Dict]):
        """Setup player objects and connect to WebSocket"""
        for user in users:
            # Get WebSocket token
            headers = {"Authorization": f"Bearer {user['token']}"}
            response = requests.post(
                f"{self.base_url}/game/websocket-token", headers=headers)

            if response.status_code == 200:
                ws_token = response.json()["websocket_token"]
                player = GamePlayer(
                    player_id=user["id"],
                    username=user["username"],
                    strategy=user["strategy"],
                    token=ws_token
                )

                await player.connect_websocket(self.base_url)
                self.players.append(player)

                # Initialize player stats
                self.player_stats[user["id"]] = PlayerStats(
                    player_id=user["id"],
                    username=user["username"],
                    strategy=user["strategy"]
                )
            else:
                print(f"Failed to get WebSocket token for {user['username']}")

    async def run_simulation(self, duration_seconds: int = 60):
        """Run the simulation for a specified duration"""
        print(
            f"Starting simulation with {len(self.players)} players for {duration_seconds} seconds...")

        # Start listening for messages from all players
        tasks = []
        for player in self.players:
            task = asyncio.create_task(
                player.listen_for_messages(self.game_results))
            tasks.append(task)

        # Let the simulation run
        await asyncio.sleep(duration_seconds)

        # Cancel all tasks
        for task in tasks:
            task.cancel()

        print("Simulation completed!")

    def analyze_results(self):
        """Analyze game results and update player statistics"""
        print("\n" + "="*60)
        print("ANALYZING SIMULATION RESULTS")
        print("="*60)

        # Process each game result
        for game_id, result in self.game_results.items():
            self.validate_game_result(result)

            # Update player stats
            player1_stats = self.player_stats.get(result.player1_id)
            player2_stats = self.player_stats.get(result.player2_id)

            if player1_stats and player2_stats:
                player1_stats.total_games += 1
                player2_stats.total_games += 1
                player1_stats.games_played.append(game_id)
                player2_stats.games_played.append(game_id)

                if result.is_draw:
                    player1_stats.draws += 1
                    player2_stats.draws += 1
                elif result.winner_id == result.player1_id:
                    player1_stats.wins += 1
                    player2_stats.losses += 1
                elif result.winner_id == result.player2_id:
                    player2_stats.wins += 1
                    player1_stats.losses += 1

        # Calculate derived statistics
        for stats in self.player_stats.values():
            if stats.total_games > 0:
                stats.win_ratio = stats.wins / stats.total_games
                stats.avg_moves_per_game = stats.total_moves / \
                    stats.total_games if stats.total_moves > 0 else 0

        self.print_statistics()

    def validate_game_result(self, result: GameResult):
        """Validate that a game result is correct"""
        try:
            # Recreate the board from moves
            board = TicTacToeBoard()

            for player_id, row, col in result.moves:
                if not board.make_move(row, col, player_id):
                    raise AssertionError(
                        f"Invalid move in game {result.game_id}: ({row}, {col}) already occupied")

            # Check winner
            actual_winner = board.check_winner()

            if result.is_draw:
                assert actual_winner is None, f"Game {result.game_id}: Marked as draw but has winner {actual_winner}"
                assert board.is_full(
                ), f"Game {result.game_id}: Marked as draw but board not full"
            elif result.winner_id:
                assert actual_winner == result.winner_id, f"Game {result.game_id}: Winner mismatch. Expected {result.winner_id}, got {actual_winner}"

            print(f"✓ Game {result.game_id} result validated successfully")

        except Exception as e:
            print(f"✗ Game {result.game_id} validation failed: {e}")

    def print_statistics(self):
        """Print comprehensive statistics"""
        print(f"\nTotal games simulated: {len(self.game_results)}")

        # Top players by win ratio
        sorted_players = sorted(self.player_stats.values(),
                                key=lambda x: (x.win_ratio, x.wins), reverse=True)

        print("\n" + "-"*50)
        print("TOP 3 PLAYERS BY WIN RATIO")
        print("-"*50)
        print(
            f"{'Rank':<4} {'Username':<12} {'Games':<6} {'W-L-D':<8} {'Win Ratio':<10}")
        print("-"*50)

        for i, stats in enumerate(sorted_players[:3], 1):
            wld = f"{stats.wins}-{stats.losses}-{stats.draws}"
            print(
                f"{i:<4} {stats.username:<12} {stats.total_games:<6} {wld:<8} {stats.win_ratio:.2%}")

        # Detailed player statistics
        print("\n" + "-"*70)
        print("DETAILED PLAYER STATISTICS")
        print("-"*70)
        print(
            f"{'Username':<12} {'Games':<6} {'Wins':<5} {'Losses':<7} {'Draws':<6} {'Win Ratio':<10}")
        print("-"*70)

        for stats in sorted_players:
            print(f"{stats.username:<12} {stats.total_games:<6} "
                  f"{stats.wins:<5} {stats.losses:<7} {stats.draws:<6} {stats.win_ratio:.2%}")


async def main():
    """Main simulation function"""
    print("Tic-Tac-Toe Game Simulation")
    print("="*40)

    # Configuration
    NUM_PLAYERS = 10  # Should be even for proper matchmaking
    SIMULATION_DURATION = 45  # seconds - longer duration for more games
    BASE_URL = "http://localhost:8000"

    simulator = GameSimulator(BASE_URL)

    try:
        # Clean up existing data
        simulator.cleanup_database()

        # Create test users
        print(f"Creating {NUM_PLAYERS} test users...")
        users = simulator.create_test_users(NUM_PLAYERS)

        if len(users) < 2:
            print("Need at least 2 users to run simulation")
            return

        # Setup players and connect to WebSocket
        print("Setting up players and connecting to WebSocket...")
        await simulator.setup_players(users)

        if len(simulator.players) < 2:
            print("Need at least 2 connected players to run simulation")
            return

        # Run simulation
        await simulator.run_simulation(SIMULATION_DURATION)

        # Analyze results
        simulator.analyze_results()

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
    except Exception as e:
        print(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close WebSocket connections
        for player in simulator.players:
            if player.websocket:
                await player.websocket.close()


if __name__ == "__main__":
    asyncio.run(main())
