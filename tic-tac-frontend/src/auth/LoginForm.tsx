import React from 'react';
import { useState } from 'react';
import { API_URL } from '../App.tsx';

function LoginForm({
	onLogin,
	switchToRegister,
}: {
	onLogin: (token: string, userID: number) => void;
	switchToRegister: () => void;
}) {
	const [formData, setFormData] = useState({ username: '', password: '' });
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');

	const handleSubmit = async () => {
		if (!formData.username || !formData.password) {
			setError('Please fill in all fields');
			return;
		}

		setLoading(true);
		setError('');

		try {
			console.log('Attempting login', {
				username: formData.username,
				password: formData.password,
			});

			const response = await fetch(`${API_URL}/user/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					username: formData.username,
					password: formData.password,
				}),
			});
			const data = await response.json();

			onLogin(data.access_token, data.id);
		} catch (err) {
			setError('Login failed. Please try again.');
		} finally {
			setLoading(false);
		}
	};

	const handleChange = (e) => {
		setFormData({ ...formData, [e.target.name]: e.target.value });
	};

	return (
		<div className="space-y-6">
			<div>
				<label className="block text-sm font-medium text-slate-700 mb-2">
					Username
				</label>
				<input
					type="text"
					name="username"
					value={formData.username}
					onChange={handleChange}
					className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
					placeholder="Enter your username"
				/>
			</div>

			<div>
				<label className="block text-sm font-medium text-slate-700 mb-2">
					Password
				</label>
				<input
					type="password"
					name="password"
					value={formData.password}
					onChange={handleChange}
					className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
					placeholder="Enter your password"
				/>
			</div>

			{error && (
				<div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
					{error}
				</div>
			)}

			<button
				onClick={handleSubmit}
				disabled={loading}
				className="w-full py-3 px-4 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors shadow-lg"
			>
				{loading ? 'Signing In...' : 'Sign In'}
			</button>

			<div className="text-center">
				<button
					onClick={switchToRegister}
					className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
				>
					Don't have an account? Sign up
				</button>
			</div>
		</div>
	);
}

export default LoginForm;
