export interface Player {
	id: number;
	username: string;
}

export interface GameStartEvent {
	type: 'GAME_START';
	game_id: number;
	player1: Player;
	player2: Player;
	turn: number;
}

export interface GameEndEvent {
	type: 'GAME_END';
	game_id: number;
	winner_id: number | undefined;
	player1: { id: number; username: string };
	player2: { id: number; username: string };
}

export interface GameMoveEvent {
	type: 'GAME_MOVE';
	game_id: number;
	// is_valid: boolean;
	turn: number | undefined;
	player_id: number | undefined;
	row: number | undefined;
	col: number | undefined;
}

export type ServerEvent = GameStartEvent | GameEndEvent | GameMoveEvent;
