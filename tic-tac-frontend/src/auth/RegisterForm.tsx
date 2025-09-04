import React from 'react';
import { useState } from 'react';
import { API_URL } from '../App.tsx';

function RegisterForm({
	onRegister,
	switchToLogin,
}: {
	onRegister: (token: string, userID: number) => void;
	switchToLogin: () => void;
}) {
	const [formData, setFormData] = useState({
		username: '',
		firstName: '',
		lastName: '',
		password: '',
		confirmPassword: '',
	});
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState('');

	const handleSubmit = async () => {
		if (
			!formData.username ||
			!formData.firstName ||
			!formData.lastName ||
			!formData.password ||
			!formData.confirmPassword
		) {
			setError('Please fill in all fields');
			return;
		}

		if (formData.password !== formData.confirmPassword) {
			setError('Passwords do not match');
			return;
		}

		setLoading(true);
		setError('');

		try {
			console.log('Attempting registration', {
				username: formData.username,
				firstName: formData.firstName,
				lastName: formData.lastName,
			});

			const response = await fetch(`${API_URL}/user/create`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					username: formData.username,
					first_name: formData.firstName,
					last_name: formData.lastName,
					password: formData.password,
				}),
			});
			if (response.status !== 200) {
				setError('Registration failed. Please try again.');
				return;
			}
			const data = await response.json();

			onRegister(data.access_token, data.id);
		} catch (err) {
			setError('Registration failed. Please try again.');
			console.error(err);
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
					placeholder="Choose a username"
				/>
			</div>

			<div>
				<label className="block text-sm font-medium text-slate-700 mb-2">
					First Name
				</label>
				<input
					type="text"
					name="firstName"
					value={formData.firstName}
					onChange={handleChange}
					className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
					placeholder="Enter your first name"
				/>
			</div>
			<div>
				<label className="block text-sm font-medium text-slate-700 mb-2">
					Last Name
				</label>
				<input
					type="text"
					name="lastName"
					value={formData.lastName}
					onChange={handleChange}
					className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
					placeholder="Enter your last name"
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
					placeholder="Create a password"
				/>
			</div>

			<div>
				<label className="block text-sm font-medium text-slate-700 mb-2">
					Confirm Password
				</label>
				<input
					type="password"
					name="confirmPassword"
					value={formData.confirmPassword}
					onChange={handleChange}
					className="w-full px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
					placeholder="Confirm your password"
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
				className="w-full py-3 px-4 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors shadow-lg"
			>
				{loading ? 'Creating Account...' : 'Create Account'}
			</button>

			<div className="text-center">
				<button
					onClick={switchToLogin}
					className="text-blue-600 hover:text-blue-700 font-medium transition-colors"
				>
					Already have an account? Sign in
				</button>
			</div>
		</div>
	);
}

export default RegisterForm;
