import { Sparkles } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";

const TransitionView: React.FC = () => {
	const [dots, setDots] = useState("");

	useEffect(() => {
		const interval = setInterval(() => {
			setDots((prev) => (prev.length >= 3 ? "" : `${prev}.`));
		}, 500);
		return () => clearInterval(interval);
	}, []);

	const messages = [
		"Analyzing your goals...",
		"Breaking down complex tasks...",
		"Filling in missing pieces with AI intelligence...",
		"Designing your quest map...",
		"Almost ready to launch!",
	];

	const [msgIndex, setMsgIndex] = useState(0);

	useEffect(() => {
		const interval = setInterval(() => {
			setMsgIndex((prev) => (prev + 1) % messages.length);
		}, 2000);
		return () => clearInterval(interval);
	}, []);

	return (
		<div className="fixed inset-0 z-50 bg-slate-900 flex flex-col items-center justify-center text-white">
			<div className="relative mb-8">
				<div className="absolute inset-0 bg-blue-500 blur-3xl opacity-20 animate-pulse"></div>
				<Sparkles className="w-20 h-20 text-blue-400 animate-bounce" />
			</div>

			<div className="text-center space-y-4 max-w-md px-6">
				<h2 className="text-2xl font-bold">Constructing Your Roadmap{dots}</h2>
				<p className="text-slate-400 text-sm h-10 transition-all duration-500 animate-in fade-in slide-in-from-bottom-2">
					{messages[msgIndex]}
				</p>
			</div>

			<div className="mt-12 flex gap-1">
				{[1, 2, 3, 4, 5].map((i) => (
					<div
						key={i}
						className={`w-2 h-2 rounded-full bg-blue-500 animate-pulse`}
						style={{ animationDelay: `${i * 0.2}s` }}
					/>
				))}
			</div>
		</div>
	);
};

export default TransitionView;
