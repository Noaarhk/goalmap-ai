import {
	CheckCircle,
	Clock,
	Crosshair,
	Play,
	Sparkles,
} from "lucide-react";
import type { RoadmapNode } from "../../../types";

interface TaskCardProps {
	task: RoadmapNode;
	isSelected: boolean;
	onClick: () => void;
}

const statusConfig = {
	pending: {
		icon: Clock,
		label: "Pending",
		dotColor: "bg-slate-500",
		textColor: "text-slate-400",
	},
	in_progress: {
		icon: Play,
		label: "In Progress",
		dotColor: "bg-blue-500 animate-pulse",
		textColor: "text-blue-400",
	},
	completed: {
		icon: CheckCircle,
		label: "Done",
		dotColor: "bg-emerald-500",
		textColor: "text-emerald-400",
	},
} as const;

export function TaskCard({ task, isSelected, onClick }: TaskCardProps) {
	const status = task.status ? statusConfig[task.status] : statusConfig.pending;
	const progress = task.progress ?? 0;
	const isDone = progress >= 100;

	const progressColor = isDone
		? "from-emerald-600 to-emerald-400"
		: progress > 0
			? "from-blue-600 to-blue-400"
			: "from-slate-700 to-slate-600";

	return (
		<button
			type="button"
			onClick={onClick}
			className={`
				group w-full text-left rounded-xl border transition-all duration-200
				${isSelected
					? "border-blue-500/60 bg-blue-500/5 ring-1 ring-blue-500/30"
					: "border-slate-700/50 bg-[#1a2436] hover:border-slate-600 hover:bg-[#1e2a3e]"
				}
				${isDone ? "opacity-75" : ""}
			`}
		>
			<div className="p-4">
				{/* Top: status + progress */}
				<div className="flex items-center justify-between mb-2.5">
					<div className="flex items-center gap-2">
						<div className={`w-2 h-2 rounded-full ${status.dotColor}`} />
						<span className={`text-[10px] font-semibold uppercase tracking-wider ${status.textColor}`}>
							{status.label}
						</span>
						{task.isAssumed && (
							<Sparkles className="w-3 h-3 text-purple-400" />
						)}
					</div>
					<span
						className={`text-xs font-bold tabular-nums ${
							isDone ? "text-emerald-400" : progress > 0 ? "text-blue-400" : "text-slate-600"
						}`}
					>
						{progress}%
					</span>
				</div>

				{/* Title */}
				<div className="flex items-start gap-2 mb-2">
					<Crosshair className="w-3.5 h-3.5 text-emerald-500/60 mt-0.5 shrink-0" />
					<p className={`text-sm font-semibold leading-snug ${isDone ? "text-slate-400 line-through" : "text-white"}`}>
						{task.label}
					</p>
				</div>

				{/* Details preview */}
				{task.details && (
					<p className="text-xs text-slate-500 line-clamp-2 ml-5.5 mb-3">
						{task.details}
					</p>
				)}

				{/* Progress bar */}
				<div className="h-1 bg-slate-700/40 rounded-full overflow-hidden">
					<div
						className={`h-full rounded-full bg-gradient-to-r ${progressColor} transition-all duration-500`}
						style={{ width: `${Math.max(progress, 1)}%` }}
					/>
				</div>

				{/* Dates */}
				{(task.startDate || task.endDate) && (
					<div className="flex items-center gap-1.5 mt-2.5 text-[10px] text-slate-600">
						<Clock className="w-3 h-3" />
						<span>
							{task.startDate || "?"} — {task.endDate || "?"}
						</span>
					</div>
				)}
			</div>
		</button>
	);
}
