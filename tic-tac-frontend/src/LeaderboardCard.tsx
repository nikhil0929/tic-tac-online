import React, { useState, useEffect } from 'react';
import { API_URL } from './App.tsx';

interface LeaderboardEntry {
	user_id: number;
	username: string;
	wins: number;
	losses: number;
	draws: number;
	efficiency: number | null;
}

const LeaderboardCard = () => {
	const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
	const [loading, setLoading] = useState(true);

	useEffect(() => {
		const fetchLeaderboard = async () => {
			try {
				const response = await fetch(`${API_URL}/game/leaderboard`);
				const data = await response.json();
				setLeaderboard(data);
			} catch (error) {
				console.error('Error fetching leaderboard:', error);
			} finally {
				setLoading(false);
			}
		};

		fetchLeaderboard();
		// Refresh leaderboard every 30 seconds
		const interval = setInterval(fetchLeaderboard, 30000);
		return () => clearInterval(interval);
	}, []);

	if (loading) {
		return (
			<div className="w-80 bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
				<h2 className="text-2xl font-bold text-slate-800 mb-4">Leaderboard</h2>
				<div className="text-center text-slate-500">Loading...</div>
			</div>
		);
	}

	return (
		<div className="w-80 bg-white rounded-2xl shadow-lg p-6 border border-slate-200">
			<h2 className="text-2xl font-bold text-slate-800 mb-4">Leaderboard</h2>
			<div className="space-y-3">
				{leaderboard.length === 0 ? (
					<div className="text-center text-slate-500">No players yet</div>
				) : (
					leaderboard.map((player, index) => (
						<div
							key={player.user_id}
							className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
						>
							<div className="flex items-center space-x-3">
								<div
									className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
										index === 0
											? 'bg-yellow-500'
											: index === 1
											? 'bg-gray-400'
											: index === 2
											? 'bg-amber-600'
											: 'bg-slate-400'
									}`}
								>
									{index + 1}
								</div>
								<div>
									<div className="font-semibold text-slate-800">
										{player.username}
									</div>
									<div className="text-xs text-slate-500">
										{player.wins}W-{player.losses}L-{player.draws}D
									</div>
								</div>
							</div>
							<div className="text-right">
								<div className="text-sm font-medium text-slate-700">
									{player.efficiency !== null
										? `${player.efficiency.toFixed(1)} avg`
										: 'N/A'}
								</div>
								<div className="text-xs text-slate-500">efficiency</div>
							</div>
						</div>
					))
				)}
			</div>
		</div>
	);
};

export default LeaderboardCard;
