import React, { useState, useEffect, useRef, use } from 'react';
import { GameClient } from './GameClient.ts';
import { API_URL } from './App.tsx';
import {
	GameEndEvent,
	GameMoveEvent,
	GameStartEvent,
	Player,
	ServerEvent,
} from './types.ts';

type Cell = number | undefined;

interface Game {
	/*
	this.game_id = game_id;
		this.player1 = player1;
		this.player2 = player2;
		this.turn = turn;
		this.game_state = [
			[undefined, undefined, undefined],
			[undefined, undefined, undefined],
			[undefined, undefined, undefined],
		];
	*/
	game_id: number;
	player1: Player;
	player2: Player;
	turn: number;
	game_state: Cell[][];
}

const Board = ({ userID }: { userID: number }) => {
	const [gameClient, setGameClient] = useState<GameClient | null>(null);
	const [game, setGame] = useState<Game | null>(null);
	const [gameStatus, setGameStatus] = useState<
		'waiting' | 'playing' | 'finished'
	>('waiting');
	const [winner, setWinner] = useState<number | null>(null);
	const [isMyTurn, setIsMyTurn] = useState(false);

	const joinMatchmaking = async () => {
		setGameStatus('waiting');
		/*
		first make a call to the first endpoint then take that token and use it in the next:
		@router.post("/api/auth/websocket-token")
async def get_websocket_token(
    current_user: User = Depends(get_current_user),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Exchange JWT for a temporary WebSocket token"""
    websocket_token = await create_websocket_token(current_user, redis_client)

    return {"websocket_token": websocket_token}

		*/
		const response = await fetch(API_URL + '/game/websocket-token', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${localStorage.getItem('token')}`,
			},
		});
		const data = await response.json();
		const client = new GameClient(
			'ws://localhost:8000/game/ws?token=' + data.websocket_token,
			(eventData: GameStartEvent) => {
				setGameStatus('playing');
				const newGame: Game = {
					game_id: eventData.game_id,
					player1: eventData.player1,
					player2: eventData.player2,
					turn: eventData.turn,
					game_state: [
						[undefined, undefined, undefined],
						[undefined, undefined, undefined],
						[undefined, undefined, undefined],
					],
				};
				setGame(newGame);
				console.log('eventData.turn is this: ', eventData.turn);
				console.log('userID is this: ', userID);
				setIsMyTurn(eventData.turn === userID);
			},
			(eventData: GameMoveEvent) => {
				setGameStatus('playing');
				console.log('eventData is this: ', eventData);
				if (
					eventData.row !== undefined &&
					eventData.col !== undefined &&
					eventData.player_id !== undefined &&
					eventData.turn !== undefined
				) {
					setGame((currentGame) => {
						if (!currentGame) return null;

						console.log('currentGame is thisssss: ', currentGame);

						// Create a new board array instead of mutating the existing one
						const newBoard = currentGame.game_state.map((row, rowIndex) =>
							rowIndex === eventData.row
								? row.map((cell, colIndex) =>
										colIndex === eventData.col ? eventData.player_id : cell
								  )
								: row
						);

						setIsMyTurn(eventData.turn === userID);
						console.log('game after update: ', {
							...currentGame,
							game_state: newBoard,
							turn: eventData.turn || 0,
						});

						return {
							...currentGame,
							game_state: newBoard,
							turn: eventData.turn || 0,
						};
					});
				}
			},
			(eventData: GameEndEvent) => {
				setGameStatus('finished');
				if (eventData.winner_id) {
					setWinner(eventData.winner_id);
				}
			}
		);
		setGameClient(client);
	};

	useEffect(() => {
		console.log('game: ', game);
		console.log('turn: ', game?.turn);
		console.log('myPlayerId: ', userID);
		console.log('isMyTurn: ', isMyTurn);
	}, [game, userID, isMyTurn]);

	const handleCellClick = (row: number, col: number) => {
		if (!gameClient || !game || gameStatus !== 'playing') {
			alert('You are not in a game!');
			return;
		}
		if (!isMyTurn) {
			alert('It is not your turn!');
			return;
		}

		// Check if cell is already taken
		if (game.game_state[row][col] !== undefined) {
			alert('Cell already taken');
			return;
		}

		// Send move to server
		gameClient.playMove(game.game_id, row, col);
	};

	const renderCell = (row: number, col: number) => {
		if (!gameClient || !game) return null;

		const value = game.game_state[row][col];

		return (
			<button
				key={`${row}-${col}`}
				className={`
					w-24 h-24 border-4 border-slate-300 bg-white hover:bg-slate-50 
					transition-all duration-200 shadow-lg
					text-4xl font-bold
					${
						isMyTurn && !value && gameStatus === 'playing'
							? 'hover:scale-105 cursor-pointer'
							: 'cursor-not-allowed'
					}
					${
						value === undefined
							? 'text-gray-400'
							: value === game.player1.id
							? 'text-blue-600'
							: 'text-red-500'
					}
				`}
				onClick={() => handleCellClick(row, col)}
				disabled={!isMyTurn || gameStatus !== 'playing'}
			>
				{!value ? '-' : value.toString()}
			</button>
		);
	};

	const getStatusMessage = () => {
		switch (gameStatus) {
			case 'waiting':
				return 'Waiting for opponent...';
			case 'playing':
				return isMyTurn ? 'Your turn' : "Opponent's turn";
			case 'finished':
				if (!winner) return 'Game ended in a draw';
				return `${winner} won! 🎉`;
			default:
				return 'Ready to play';
		}
	};

	return (
		<div className="flex flex-col items-center justify-center min-h-screen p-8">
			<div className="bg-white rounded-3xl shadow-2xl p-8 border border-slate-200">
				{/* Header */}
				<div className="text-center mb-8">
					<h1 className="text-4xl font-bold text-slate-800 mb-2">
						Tic Tac Toe
					</h1>
					{gameClient && game && (
						<div className="text-lg text-slate-600 mb-4">
							<div>Player 1: {game.player1.username}</div>
							<div>Player 2: {game.player2.username}</div>
							<div className="mt-2">
								Playing as:{' '}
								<span
									className={`font-bold ${
										game.player1.id === userID
											? 'text-blue-600'
											: 'text-red-500'
									}`}
								>
									{userID}
								</span>
							</div>
						</div>
					)}
					<div
						className={`text-xl font-semibold p-3 rounded-xl ${
							gameStatus === 'playing' && isMyTurn
								? 'bg-green-100 text-green-800'
								: gameStatus === 'playing'
								? 'bg-yellow-100 text-yellow-800'
								: 'bg-slate-100 text-slate-600'
						}`}
					>
						{getStatusMessage()}
					</div>
				</div>

				{/* Game Board */}
				<div className="grid grid-cols-3 gap-2 mb-8 p-4 bg-slate-100 rounded-2xl">
					{Array(9)
						.fill(null)
						.map((_, index) => renderCell(index % 3, Math.floor(index / 3)))}
				</div>

				{/* Control Buttons */}
				<div className="flex gap-4 justify-center">
					{gameStatus === 'waiting' && (
						<button
							onClick={joinMatchmaking}
							className="px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg"
						>
							Find Game
						</button>
					)}
				</div>

				{/* Debug Info */}
				<div className="mt-8 p-4 bg-slate-50 rounded-xl">
					<h3 className="font-semibold text-slate-700 mb-2">
						Debug Info (Remove in production)
					</h3>
					<div className="text-sm text-slate-600 space-y-1">
						<div>Game Status: {gameStatus}</div>
						<div>Is My Turn: {isMyTurn ? 'Yes' : 'No'}</div>
						<div>Winner: {winner || 'None'}</div>
						<div>Game ID: {game?.game_id || 'None'}</div>
					</div>
				</div>
			</div>
		</div>
	);
};

export default Board;
