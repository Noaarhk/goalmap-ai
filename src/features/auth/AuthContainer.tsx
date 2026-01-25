import { Loader2, LogIn, Swords, UserPlus } from "lucide-react";
import { useState } from "react";
import { useAuthStore } from "../../stores/useAuthStore";

export function AuthContainer() {
	const { signIn, signUp, isLoading } = useAuthStore();

	const [isSignUp, setIsSignUp] = useState(false);
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [error, setError] = useState<string | null>(null);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setError(null);

		const result = isSignUp
			? await signUp(email, password)
			: await signIn(email, password);

		if (result.error) {
			setError(result.error);
		}
	};

	return (
		<div className="flex h-screen w-screen bg-[#101722] items-center justify-center">
			{/* Background Pattern */}
			<div className="absolute inset-0 bg-grid-pattern opacity-10" />

			{/* Auth Card */}
			<div className="relative z-10 w-full max-w-md mx-4">
				<div className="bg-[#1a2436] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
					{/* Header */}
					<div className="p-8 text-center border-b border-slate-700 bg-[#101722]/50">
						<div className="inline-flex p-3 bg-blue-600 rounded-xl shadow-[0_0_20px_rgba(59,130,246,0.5)] mb-4">
							<Swords className="w-8 h-8 text-white" />
						</div>
						<h1 className="font-black text-2xl tracking-tighter uppercase italic text-white">
							QuestForge <span className="text-blue-500">AI</span>
						</h1>
						<p className="text-xs text-slate-500 mt-2 uppercase tracking-widest">
							{isSignUp ? "Create Your Account" : "Welcome Back, Adventurer"}
						</p>
					</div>

					{/* Form */}
					<form onSubmit={handleSubmit} className="p-8 space-y-6">
						{error && (
							<div className="bg-red-900/20 border border-red-500/30 rounded-xl p-4 text-sm text-red-400">
								{error}
							</div>
						)}

						<div className="space-y-4">
							<div>
								<label
									htmlFor="email"
									className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2"
								>
									Email
								</label>
								<input
									id="email"
									type="email"
									value={email}
									onChange={(e) => setEmail(e.target.value)}
									placeholder="hero@questforge.ai"
									required
									className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
								/>
							</div>

							<div>
								<label
									htmlFor="password"
									className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2"
								>
									Password
								</label>
								<input
									id="password"
									type="password"
									value={password}
									onChange={(e) => setPassword(e.target.value)}
									placeholder="••••••••"
									required
									minLength={6}
									className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
								/>
							</div>
						</div>

						<button
							type="submit"
							disabled={isLoading}
							className="w-full flex items-center justify-center gap-2 py-4 bg-blue-600 text-white rounded-xl font-black text-sm uppercase tracking-widest shadow-lg hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all"
						>
							{isLoading ? (
								<Loader2 className="w-5 h-5 animate-spin" />
							) : isSignUp ? (
								<>
									<UserPlus className="w-5 h-5" />
									Create Account
								</>
							) : (
								<>
									<LogIn className="w-5 h-5" />
									Enter the Realm
								</>
							)}
						</button>

						{!isSignUp && (
							<div className="relative py-4">
								<div className="absolute inset-0 flex items-center">
									<div className="w-full border-t border-slate-700" />
								</div>
								<div className="relative flex justify-center text-xs uppercase">
									<span className="bg-[#1a2436] px-2 text-slate-500 font-bold tracking-widest">
										Or continue with
									</span>
								</div>
							</div>
						)}

						{!isSignUp && (
							<button
								type="button"
								onClick={async () => {
									const result = await useAuthStore
										.getState()
										.signInWithGoogle();
									if (result.error) setError(result.error);
								}}
								disabled={isLoading}
								className="w-full flex items-center justify-center gap-3 py-3 bg-slate-900 border border-slate-700 text-white rounded-xl font-bold text-sm tracking-wide hover:bg-slate-800 transition-all active:scale-95"
							>
								<svg className="w-5 h-5" viewBox="0 0 24 24">
									<title>Google</title>
									<path
										fill="currentColor"
										d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
									/>
									<path
										fill="currentColor"
										d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
									/>
									<path
										fill="currentColor"
										d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
									/>
									<path
										fill="currentColor"
										d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
									/>
								</svg>
								Google
							</button>
						)}
					</form>

					{/* Toggle */}
					<div className="px-8 pb-8">
						<button
							type="button"
							onClick={() => {
								setIsSignUp(!isSignUp);
								setError(null);
							}}
							className="w-full text-center text-sm text-slate-400 hover:text-blue-400 transition-colors"
						>
							{isSignUp
								? "Already have an account? Sign In"
								: "New adventurer? Create Account"}
						</button>
					</div>
				</div>
			</div>
		</div>
	);
}
