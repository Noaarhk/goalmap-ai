import { Clock, Loader2, Sparkles, Target } from "lucide-react";
import type { RoadmapNode } from "../../../types";

interface GoalHeroProps {
	goal: RoadmapNode;
	totalProgress: number;
	milestoneCount: number;
	taskCount: number;
	isSyncing: boolean;
}

export function GoalHero({
	goal,
	totalProgress,
	milestoneCount,
	taskCount,
	isSyncing,
}: GoalHeroProps) {
	const progressColor =
		totalProgress >= 100
			? "from-emerald-600 to-emerald-400"
			: totalProgress > 0
				? "from-blue-600 to-cyan-400"
				: "from-slate-600 to-slate-500";

	const progressTextColor =
		totalProgress >= 100
			? "text-emerald-400"
			: totalProgress > 0
				? "text-blue-400"
				: "text-slate-500";

	return (
		<div className="relative overflow-hidden rounded-2xl border border-slate-700/60 bg-gradient-to-br from-[#1a2436] to-[#101722] p-8">
			{/* Decorative gradient blob */}
			<div className="absolute -top-20 -right-20 w-60 h-60 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
			<div className="absolute -bottom-10 -left-10 w-40 h-40 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

			<div className="relative z-10">
				{/* Top row: badge + sync indicator */}
				<div className="flex items-center gap-3 mb-4">
					<div className="flex items-center gap-2 px-3 py-1.5 bg-amber-500/10 border border-amber-500/25 rounded-full">
						<Target className="w-4 h-4 text-amber-400" />
						<span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
							Goal
						</span>
					</div>
					{goal.isAssumed && (
						<span className="flex items-center gap-1 px-2 py-1 bg-purple-500/10 border border-purple-500/30 rounded-full text-[10px] text-purple-400 font-medium">
							<Sparkles className="w-3 h-3" />
							AI Generated
						</span>
					)}
					{isSyncing && (
						<div className="flex items-center gap-1.5 text-[11px] text-emerald-400 ml-auto">
							<Loader2 className="w-3.5 h-3.5 animate-spin" />
							<span>Syncing...</span>
						</div>
					)}
				</div>

				{/* Title */}
				<h1 className="text-2xl font-extrabold text-white leading-tight mb-2">
					{goal.label}
				</h1>

				{/* Details */}
				{goal.details && (
					<p className="text-sm text-slate-400 leading-relaxed mb-6 max-w-2xl">
						{goal.details}
					</p>
				)}

				{/* Stats row */}
				<div className="flex items-end gap-8 mb-5">
					<div>
						<span className={`text-4xl font-black ${progressTextColor}`}>
							{totalProgress}%
						</span>
						<span className="text-sm text-slate-500 ml-2">complete</span>
					</div>
					<div className="flex gap-6 pb-1">
						<div className="text-center">
							<span className="text-lg font-bold text-white">
								{milestoneCount}
							</span>
							<p className="text-[10px] text-slate-500 uppercase tracking-wider">
								Milestones
							</p>
						</div>
						<div className="text-center">
							<span className="text-lg font-bold text-white">{taskCount}</span>
							<p className="text-[10px] text-slate-500 uppercase tracking-wider">
								Tasks
							</p>
						</div>
					</div>
				</div>

				{/* Progress bar */}
				<div className="h-2.5 bg-slate-700/50 rounded-full overflow-hidden">
					<div
						className={`h-full rounded-full bg-gradient-to-r ${progressColor} transition-all duration-700 ease-out`}
						style={{ width: `${Math.max(totalProgress, 1)}%` }}
					/>
				</div>

				{/* Date range */}
				{(goal.startDate || goal.endDate) && (
					<div className="flex items-center gap-2 mt-4 text-xs text-slate-500">
						<Clock className="w-3.5 h-3.5" />
						<span>
							{goal.startDate || "?"} — {goal.endDate || "?"}
						</span>
					</div>
				)}
			</div>
		</div>
	);
}
