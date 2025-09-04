import React from 'react';
import LoginForm from './LoginForm.tsx';
import RegisterForm from './RegisterForm.tsx';

const AuthScreen = ({
	isLogin,
	onLogin,
	onRegister,
	onToggle,
}: {
	isLogin: boolean;
	onLogin: (token: string, userID: number) => void;
	onRegister: (token: string, userID: number) => void;
	onToggle: (isLogin: boolean) => void;
}) => {
	return (
		<div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-100 via-white to-purple-100 p-8">
			<div className="w-full max-w-md">
				<div className="bg-white rounded-3xl shadow-2xl p-8 border border-slate-200">
					<div className="text-center mb-8">
						<h1 className="text-3xl font-bold text-slate-800 mb-2">
							{isLogin ? 'Welcome Back' : 'Join the Game'}
						</h1>
						<p className="text-slate-600">
							{isLogin
								? 'Sign in to play Tic Tac Toe'
								: 'Create an account to get started'}
						</p>
					</div>

					{isLogin ? (
						<LoginForm
							onLogin={onLogin}
							switchToRegister={() => onToggle(false)}
						/>
					) : (
						<RegisterForm
							onRegister={onRegister}
							switchToLogin={() => onToggle(true)}
						/>
					)}
				</div>
			</div>
		</div>
	);
};

export default AuthScreen;
