import {
	CheckCircle,
	Clock,
	Crosshair,
	Play,
	Sparkles,
	Target,
	Trophy,
} from "lucide-react";
import { memo } from "react";
import { Handle, Position } from "reactflow";
import type { RoadmapNode } from "../../../types";

interface RoadmapCardNodeProps {
	data: RoadmapNode;
	selected: boolean;
}

const typeConfig = {
	goal: {
		icon: Target,
		label: "Goal",
		borderColor: "border-l-amber-400",
		bgColor: "bg-amber-500/5",
		iconColor: "text-amber-400",
		badgeBg: "bg-amber-500/10",
		badgeText: "text-amber-400",
		badgeBorder: "border-amber-500/30",
	},
	milestone: {
		icon: Trophy,
		label: "Milestone",
		borderColor: "border-l-blue-500",
		bgColor: "bg-blue-500/5",
		iconColor: "text-blue-400",
		badgeBg: "bg-blue-500/10",
		badgeText: "text-blue-400",
		badgeBorder: "border-blue-500/30",
	},
	task: {
		icon: Crosshair,
		label: "Task",
		borderColor: "border-l-emerald-500",
		bgColor: "bg-emerald-500/5",
		iconColor: "text-emerald-400",
		badgeBg: "bg-emerald-500/10",
		badgeText: "text-emerald-400",
		badgeBorder: "border-emerald-500/30",
	},
} as const;

const statusConfig = {
	pending: {
		icon: Clock,
		label: "Pending",
		bg: "bg-slate-500/10",
		text: "text-slate-400",
		border: "border-slate-500/30",
	},
	in_progress: {
		icon: Play,
		label: "In Progress",
		bg: "bg-blue-500/10",
		text: "text-blue-400",
		border: "border-blue-500/30",
		pulse: true,
	},
	completed: {
		icon: CheckCircle,
		label: "Done",
		bg: "bg-emerald-500/10",
		text: "text-emerald-400",
		border: "border-emerald-500/30",
	},
} as const;

function RoadmapCardNode({ data, selected }: RoadmapCardNodeProps) {
	const config = typeConfig[data.type] || typeConfig.task;
	const status = data.status ? statusConfig[data.status] : null;
	const Icon = config.icon;
	const StatusIcon = status?.icon;

	const assumedStyles = data.isAssumed
		? "border-l-purple-500 border-dashed"
		: config.borderColor;

	const width =
		data.type === "goal"
			? "w-[280px]"
			: data.type === "milestone"
				? "w-[260px]"
				: "w-[240px]";

	return (
		<div
			className={`${width} rounded-xl border border-slate-700/60 border-l-[3px] ${assumedStyles} ${config.bgColor} bg-[#1a2436] shadow-lg transition-all duration-200 hover:shadow-xl hover:shadow-black/20 ${selected ? "ring-2 ring-blue-500/60 shadow-blue-500/10" : ""}`}
		>
			<Handle type="target" position={Position.Top} className="opacity-0" />

			{/* Header */}
			<div className="flex items-center justify-between px-4 pt-3 pb-2">
				<div className="flex items-center gap-2">
					<Icon
						className={`w-4 h-4 ${data.isAssumed ? "text-purple-400" : config.iconColor}`}
					/>
					<span
						className={`text-[10px] font-bold uppercase tracking-wider ${data.isAssumed ? "text-purple-400" : config.badgeText}`}
					>
						{config.label}
					</span>
					{data.isAssumed && (
						<span className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500/10 border border-purple-500/30 rounded text-[9px] text-purple-400">
							<Sparkles className="w-3 h-3" />
							AI
						</span>
					)}
				</div>
				{status && StatusIcon && (
					<span
						className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-semibold border ${status.bg} ${status.text} ${status.border} ${"pulse" in status && status.pulse ? "animate-pulse" : ""}`}
					>
						<StatusIcon className="w-3 h-3" />
						{status.label}
					</span>
				)}
			</div>

			{/* Title & Detail */}
			<div className="px-4 pb-2">
				<p
					className={`font-bold text-white leading-snug ${data.type === "goal" ? "text-sm" : "text-xs"}`}
				>
					{data.label}
				</p>
				{data.details && (
					<p className="text-[11px] text-slate-400 mt-1 line-clamp-1">
						{data.details}
					</p>
				)}
			</div>

			{/* Progress Bar - Always visible */}
			<div className="px-4 pb-3">
				<div className="flex items-center gap-2">
					<div className="flex-1 h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
						<div
							className={`h-full rounded-full transition-all duration-500 ${
								(data.progress ?? 0) >= 100
									? "bg-gradient-to-r from-emerald-600 to-emerald-400"
									: (data.progress ?? 0) > 0
										? "bg-gradient-to-r from-blue-600 to-blue-400"
										: "bg-slate-600"
							}`}
							style={{ width: `${Math.max(data.progress ?? 0, 2)}%` }}
						/>
					</div>
					<span className={`text-[10px] font-bold min-w-[32px] text-right ${
						(data.progress ?? 0) >= 100
							? "text-emerald-400"
							: (data.progress ?? 0) > 0
								? "text-blue-400"
								: "text-slate-500"
					}`}>
						{data.progress ?? 0}%
					</span>
				</div>
			</div>

			{/* Dates (compact) */}
			{(data.startDate || data.endDate) && (
				<div className="px-4 pb-3 flex items-center gap-2 text-[10px] text-slate-500">
					<Clock className="w-3 h-3" />
					<span>
						{data.startDate || "?"} — {data.endDate || "?"}
					</span>
				</div>
			)}

			<Handle
				type="source"
				position={Position.Bottom}
				className="opacity-0"
			/>
		</div>
	);
}

export default memo(RoadmapCardNode);
