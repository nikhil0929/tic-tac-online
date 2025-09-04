import {
	GameEndEvent,
	GameMoveEvent,
	GameStartEvent,
	ServerEvent,
} from './types';

export class GameClient {
	public socket: WebSocket | null = null;
	private url: string | undefined = undefined;
	private onGameStart?: (eventData: GameStartEvent) => void;
	private onGameMove?: (eventData: GameMoveEvent) => void;
	private onGameEnd?: (eventData: GameEndEvent) => void;
	constructor(
		url: string | undefined,
		onGameStart?: (eventData: GameStartEvent) => void,
		onGameMove?: (eventData: GameMoveEvent) => void,
		onGameEnd?: (eventData: GameEndEvent) => void
	) {
		if (!url) {
			url = 'ws://localhost:8000/ws';
		}
		this.socket = new WebSocket(url);
		this.url = url;
		this.onGameStart = onGameStart;
		this.onGameMove = onGameMove;
		this.onGameEnd = onGameEnd;
		this.socket.onopen = this.onOpen.bind(this);
		this.socket.onmessage = this.onMessage.bind(this);
		this.socket.onerror = this.onError.bind(this);
		this.socket.onclose = this.onClose.bind(this);
	}

	playMove(gameId: number, row: number, col: number) {
		this.sendMessage({
			type: 'GAME_MOVE',
			game_id: gameId,
			row: row,
			col: col,
			// player_id: undefined, // backend endpoint already parses the player_id and attatches it to message before sending to opponent
		});
	}

	sendMessage(data: unknown) {
		const payload = typeof data === 'string' ? data : JSON.stringify(data);
		if (this.socket?.readyState === WebSocket.OPEN) {
			this.socket.send(payload);
		} else {
			console.warn(
				'WebSocket is not open. ReadyState:',
				this.socket?.readyState
			);
		}
	}

	private onOpen(event: Event) {
		console.log('WebSocket connection opened:', event);
		// Now that the connection is open, send a message.
		// this.sendMessage('Hello, server!');
	}

	private onMessage(event: MessageEvent) {
		let parsed: ServerEvent | undefined;
		try {
			parsed = JSON.parse(event.data);
		} catch {
			console.error('Failed to parse message from server');
			return;
		}
		if (!parsed) {
			return;
		}
		console.log('type is: ', parsed.type);
		switch (parsed.type) {
			case 'GAME_START':
				console.log(`game start: ${parsed}`);
				// this.game = new Game(
				// 	parsed.game_id,
				// 	parsed.player1,
				// 	parsed.player2,
				// 	parsed.turn
				// );
				console.log('onGameStart: ', this.onGameStart);
				if (this.onGameStart) {
					console.log('calling onGameStart with: ', parsed);
					this.onGameStart(parsed);
				}
				break;
			case 'GAME_MOVE':
				console.log(`game move: ${parsed}`);
				// if (this.game && parsed.row && parsed.col && parsed.player_id) {
				// 	this.game.markCell(parsed.row, parsed.col, parsed.player_id);
				// }
				console.log('onGameMove: ', this.onGameMove);
				if (this.onGameMove) {
					console.log('calling onGameMove with: ', parsed);
					this.onGameMove(parsed);
				}
				break;
			case 'GAME_END':
				console.log(`game end: ${parsed}`);
				if (this.onGameEnd) {
					this.onGameEnd(parsed);
				}
				break;
			default:
				console.error(`unknown event type`);
				break;
		}
	}

	private onError(event: Event) {
		console.error(`error: ${event}`);
	}

	private onClose(event: CloseEvent) {
		if (event.wasClean) {
			console.log(
				`Connection closed cleanly, code=${event.code}, reason=${event.reason}`
			);
		} else {
			console.warn('Connection died'); // e.g. server process killed or network down
		}
	}
}
