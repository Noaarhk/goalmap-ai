import {
	CheckCircle,
	ChevronDown,
	ChevronRight,
	Clock,
	Play,
	Sparkles,
	Trophy,
} from "lucide-react";
import { useState } from "react";
import type { RoadmapNode } from "../../../types";
import { TaskCard } from "./TaskCard";

interface MilestoneSectionProps {
	milestone: RoadmapNode;
	tasks: RoadmapNode[];
	isLast: boolean;
	selectedNodeId: string | null;
	onNodeSelect: (id: string) => void;
}

const statusConfig = {
	pending: {
		icon: Clock,
		label: "Pending",
		ringColor: "border-slate-600",
		bgColor: "bg-slate-800",
		textColor: "text-slate-400",
		lineColor: "from-slate-600/50",
	},
	in_progress: {
		icon: Play,
		label: "In Progress",
		ringColor: "border-blue-500",
		bgColor: "bg-blue-500/10",
		textColor: "text-blue-400",
		lineColor: "from-blue-500/50",
	},
	completed: {
		icon: CheckCircle,
		label: "Done",
		ringColor: "border-emerald-500",
		bgColor: "bg-emerald-500/10",
		textColor: "text-emerald-400",
		lineColor: "from-emerald-500/50",
	},
} as const;

export function MilestoneSection({
	milestone,
	tasks,
	isLast,
	selectedNodeId,
	onNodeSelect,
}: MilestoneSectionProps) {
	const [isExpanded, setIsExpanded] = useState(true);
	const status = milestone.status
		? statusConfig[milestone.status]
		: statusConfig.pending;
	const progress = milestone.progress ?? 0;
	const isDone = progress >= 100;
	const StatusIcon = status.icon;

	const completedTasks = tasks.filter((t) => (t.progress ?? 0) >= 100).length;

	return (
		<div className="relative flex gap-6">
			{/* Timeline track */}
			<div className="flex flex-col items-center shrink-0 w-10">
				{/* Milestone marker */}
				<button
					type="button"
					onClick={() => onNodeSelect(milestone.id)}
					className={`
						relative z-10 w-10 h-10 rounded-full border-2 ${status.ringColor} ${status.bgColor}
						flex items-center justify-center transition-all duration-200
						hover:scale-110 hover:shadow-lg
						${selectedNodeId === milestone.id ? "ring-2 ring-blue-500/50 ring-offset-2 ring-offset-[#101722]" : ""}
					`}
				>
					{isDone ? (
						<CheckCircle className="w-5 h-5 text-emerald-400" />
					) : (
						<Trophy className="w-5 h-5 text-blue-400" />
					)}
				</button>

				{/* Vertical line */}
				{!isLast && (
					<div
						className={`flex-1 w-0.5 bg-gradient-to-b ${status.lineColor} to-slate-800/30 min-h-[40px]`}
					/>
				)}
			</div>

			{/* Content */}
			<div className="flex-1 pb-10 min-w-0">
				{/* Milestone header */}
				<div className="mb-4">
					<button
						type="button"
						onClick={() => setIsExpanded(!isExpanded)}
						className="flex items-center gap-3 group w-full text-left"
					>
						<div className="flex-1 min-w-0">
							<div className="flex items-center gap-2 mb-1">
								<span
									className={`text-[10px] font-bold uppercase tracking-wider ${status.textColor}`}
								>
									Milestone
								</span>
								{milestone.isAssumed && (
									<Sparkles className="w-3 h-3 text-purple-400" />
								)}
								<StatusIcon className={`w-3 h-3 ${status.textColor}`} />
							</div>
							<h3 className={`text-lg font-bold leading-tight ${isDone ? "text-slate-400 line-through" : "text-white"}`}>
								{milestone.label}
							</h3>
						</div>

						{/* Right side: progress + chevron */}
						<div className="flex items-center gap-3 shrink-0">
							<div className="text-right">
								<span
									className={`text-sm font-bold tabular-nums ${
										isDone ? "text-emerald-400" : progress > 0 ? "text-blue-400" : "text-slate-600"
									}`}
								>
									{progress}%
								</span>
								<p className="text-[10px] text-slate-600">
									{completedTasks}/{tasks.length} tasks
								</p>
							</div>
							{isExpanded ? (
								<ChevronDown className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
							) : (
								<ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300 transition-colors" />
							)}
						</div>
					</button>

					{/* Milestone details & dates */}
					{milestone.details && (
						<p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
							{milestone.details}
						</p>
					)}
			{(milestone.startDate || milestone.endDate) && (
				<div className="flex items-center gap-1.5 mt-2 text-[10px] text-slate-600">
					<Clock className="w-3 h-3" />
					<span>
						{milestone.startDate || "?"} — {milestone.endDate || "?"}
					</span>
				</div>
			)}

					{/* Milestone progress bar */}
					<div className="mt-3 h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
						<div
							className={`h-full rounded-full transition-all duration-500 ${
								isDone
									? "bg-gradient-to-r from-emerald-600 to-emerald-400"
									: progress > 0
										? "bg-gradient-to-r from-blue-600 to-cyan-400"
										: "bg-slate-700"
							}`}
							style={{ width: `${Math.max(progress, 1)}%` }}
						/>
					</div>
				</div>

				{/* Tasks grid */}
				{isExpanded && tasks.length > 0 && (
					<div className="grid grid-cols-1 md:grid-cols-2 gap-3 animate-in fade-in slide-in-from-top-2 duration-200">
						{tasks.map((task) => (
							<TaskCard
								key={task.id}
								task={task}
								isSelected={selectedNodeId === task.id}
								onClick={() => onNodeSelect(task.id)}
							/>
						))}
					</div>
				)}

				{isExpanded && tasks.length === 0 && (
					<p className="text-xs text-slate-600 italic py-2">
						No tasks under this milestone
					</p>
				)}
			</div>
		</div>
	);
}
