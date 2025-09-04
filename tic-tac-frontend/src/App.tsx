import './App.css';
import Board from './Board.tsx';
import React, { useState, useEffect } from 'react';
import AuthScreen from './auth/AuthScreen.tsx';
import LeaderboardCard from './LeaderboardCard.tsx';

export const API_URL = 'http://localhost:8000';
function App() {
	const [isAuthenticated, setIsAuthenticated] = useState(false);
	const [isLogin, setIsLogin] = useState(true);
	const [userID, setUserID] = useState<number | null>();

	// Check for existing token on component mount
	useEffect(() => {
		const token = localStorage.getItem('token');
		const currentUserID = localStorage.getItem('userID');
		if (token) {
			setIsAuthenticated(true);
			setUserID(currentUserID ? parseInt(currentUserID) : null);
		}
	}, []);

	const handleLogin = (token: string, userID: number) => {
		console.log('✅ Login successful, token received');
		localStorage.setItem('token', token);
		localStorage.setItem('userID', userID.toString());
		setIsAuthenticated(true);
	};

	const handleRegister = (token: string, userID: number) => {
		console.log('✅ Registration successful, token received');
		localStorage.setItem('token', token);
		localStorage.setItem('userID', userID.toString());
		setIsAuthenticated(true);
	};

	console.log('✅ User ID isss: ', userID);
	if (isAuthenticated && userID) {
		return (
			<div className="App flex min-h-screen bg-gradient-to-br from-blue-100 via-white to-purple-100">
				<div className="p-8">
					<LeaderboardCard />
				</div>
				<div className="flex-1">
					<Board userID={userID} />
				</div>
			</div>
		);
	}

	return (
		<div className="App">
			<AuthScreen
				isLogin={isLogin}
				onLogin={handleLogin}
				onRegister={handleRegister}
				onToggle={setIsLogin}
			/>
		</div>
	);
}

export default App;
