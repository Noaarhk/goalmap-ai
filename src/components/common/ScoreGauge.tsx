import { Loader2, Sparkles } from "lucide-react";
import type React from "react";

interface ScoreGaugeProps {
	score: number;
	readinessTips?: string[];
	successTips?: string[];
	isCalculating?: boolean;
}

const ScoreGauge: React.FC<ScoreGaugeProps> = ({
	score,
	readinessTips = [],
	successTips = [],
	isCalculating = false,
}) => {
	const getLevel = () => {
		if (score < 25) return 1;
		if (score < 50) return 2;
		if (score < 75) return 3;
		return 4;
	};

	const getStatus = () => {
		if (isCalculating) return "Analyzing Response...";
		if (score < 30) return "Gathering Intelligence";
		if (score < 70) return "Drafting Blueprint";
		return "Ready for Conquest";
	};

	return (
		<div
			className={`bg-[#1a2436] border border-slate-700/50 p-6 rounded-2xl shadow-xl space-y-3 transition-all duration-300 ${isCalculating ? "border-blue-500/50 shadow-[0_0_20px_rgba(59,130,246,0.2)]" : ""}`}
		>
			<div className="flex justify-between items-end">
				<div className="space-y-1">
					<h3
						className={`text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2 ${isCalculating ? "text-amber-400" : "text-blue-500"}`}
					>
						{isCalculating && <Loader2 className="w-3 h-3 animate-spin" />}
						{getStatus()}
					</h3>
					<p className="text-xl font-black text-white">
						Readiness Level {getLevel()}
					</p>
				</div>
				<div className="text-right">
					{isCalculating ? (
						<span className="text-2xl font-black text-slate-400 animate-pulse">
							--
						</span>
					) : (
						<span className="text-2xl font-black text-white">{score}</span>
					)}
					<span className="text-sm font-bold text-slate-500">/100 XP</span>
				</div>
			</div>

			<div className="relative h-6 w-full bg-[#101722] rounded-full border border-slate-800 p-1 shadow-inner overflow-hidden">
				{/* Fill */}
				<div
					className={`h-full bg-gradient-to-r from-blue-700 via-blue-500 to-blue-400 rounded-full transition-all duration-1000 ease-out relative group ${isCalculating ? "animate-pulse" : ""}`}
					style={{ width: isCalculating ? "100%" : `${score}%` }}
				>
					{/* Shine effect */}
					<div className="absolute inset-0 bg-white/10 bg-bar-grid opacity-30"></div>
					<div className="absolute top-0 right-0 h-full w-4 bg-white/20 blur-sm"></div>
					{/* Scanning effect when calculating */}
					{isCalculating && (
						<div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"></div>
					)}
				</div>
			</div>

			{/* Readiness Level Up Tips */}
			{!isCalculating && readinessTips.length > 0 && (
				<div className="mt-6 space-y-3 animate-in fade-in slide-in-from-top-2 duration-500">
					<div className="flex items-center gap-2 text-blue-400">
						<div className="p-1 bg-blue-400/10 rounded-lg">
							<Sparkles className="w-4 h-4" />
						</div>
						<h4 className="text-[10px] font-black uppercase tracking-[0.2em]">
							Readiness Level Up Guide
						</h4>
					</div>
					<div className="grid gap-2">
						{readinessTips.map((tip, i) => (
							<div
								key={`${i}-${tip}`}
								className="text-xs text-slate-300 bg-blue-950/20 border border-blue-500/20 p-3 rounded-xl leading-relaxed"
							>
								{tip}
							</div>
						))}
					</div>
				</div>
			)}

			{/* Success Tips */}
			{!isCalculating && successTips.length > 0 && (
				<div className="mt-6 space-y-3 animate-in fade-in slide-in-from-top-2 duration-500">
					<div className="flex items-center gap-2 text-amber-400">
						<div className="p-1 bg-amber-400/10 rounded-lg">
							<svg
								className="w-4 h-4"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
								aria-hidden="true"
							>
								<title>Lightbulb icon</title>
								<path
									strokeLinecap="round"
									strokeLinejoin="round"
									strokeWidth={2}
									d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
								/>
							</svg>
						</div>
						<h4 className="text-[10px] font-black uppercase tracking-[0.2em]">
							Tips for Success
						</h4>
					</div>
					<div className="grid gap-2">
						{successTips.map((tip, i) => (
							<div
								key={`${i}-${tip}`}
								className="text-xs text-slate-300 bg-slate-800/30 border border-slate-700/30 p-3 rounded-xl leading-relaxed"
							>
								{tip}
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	);
};

export default ScoreGauge;
