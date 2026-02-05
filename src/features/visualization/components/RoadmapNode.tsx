import { Crosshair, Sparkles, Target, Trophy } from "lucide-react";
import { memo } from "react";
import { Handle, Position } from "reactflow";

const RoadmapNode = ({ data }: any) => {
	const isAssumed = data.is_assumed;
	const isGoal = data.type === "goal";
	const isMilestone = data.type === "milestone";
	const isAction = data.type === "action";

	// Size classes based on node type
	const sizeClass = isGoal
		? "w-24 h-24"
		: isMilestone
			? "w-20 h-20"
			: "w-12 h-12";

	// Color classes based on node type
	const getGlowColor = () => {
		if (isAssumed) return "bg-purple-600";
		if (isGoal) return "bg-amber-500";
		if (isMilestone) return "bg-blue-600";
		return "bg-emerald-600";
	};

	const getBorderColor = () => {
		if (isAssumed) return "border-purple-500/50 border-dashed";
		if (isGoal) return "border-amber-400";
		if (isMilestone) return "border-blue-500";
		return "border-emerald-500";
	};

	const getIcon = () => {
		if (isGoal) {
			return (
				<Target
					className={`w-10 h-10 ${isAssumed ? "text-purple-400" : "text-amber-400"}`}
				/>
			);
		}
		if (isMilestone) {
			return (
				<Trophy
					className={`w-8 h-8 ${isAssumed ? "text-purple-400" : "text-blue-400"}`}
				/>
			);
		}
		// Action node
		return (
			<Crosshair
				className={`w-5 h-5 ${isAssumed ? "text-purple-400" : "text-emerald-400"}`}
			/>
		);
	};

	const getLabelColor = () => {
		if (isAssumed) return "border-purple-900/50 text-purple-200";
		if (isGoal) return "border-amber-900/50 text-amber-100";
		if (isMilestone) return "border-slate-800 text-white";
		return "border-emerald-900/50 text-emerald-100";
	};

	const getTypeLabel = () => {
		if (isGoal) return "Main Goal";
		if (isMilestone) return "Milestone";
		return null; // Actions don't show type label
	};

	return (
		<div className="group flex flex-col items-center gap-3">
			<Handle type="target" position={Position.Top} className="opacity-0" />

			<div
				className={`relative flex items-center justify-center transition-all duration-300 group-hover:scale-110 ${sizeClass}`}
			>
				{/* Glow Ring */}
				<div
					className={`absolute inset-0 rounded-full blur-md opacity-40 transition-opacity group-hover:opacity-80 ${getGlowColor()}`}
				/>

				{/* Main Circle */}
				<div
					className={`relative w-full h-full rounded-full border-[3px] flex items-center justify-center bg-[#1a2436] shadow-2xl ${getBorderColor()}`}
				>
					{getIcon()}

					{/* AI Badge */}
					{isAssumed && (
						<div className="absolute -top-1 -right-1 p-1 bg-purple-600 rounded-full border border-purple-300 shadow-lg animate-bounce">
							<Sparkles className="w-3 h-3 text-white" />
						</div>
					)}
				</div>
			</div>

			{/* Label Box */}
			<div
				className={`px-4 py-2 rounded-xl border bg-[#101722]/90 backdrop-blur-sm shadow-xl transition-all group-hover:border-blue-500/50 ${getLabelColor()}`}
			>
				{getTypeLabel() && (
					<p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 text-center mb-0.5">
						{getTypeLabel()}
					</p>
				)}
				<p
					className={`font-bold whitespace-nowrap text-center ${isAction ? "text-[10px]" : isGoal ? "text-sm" : "text-xs"}`}
				>
					{data.label}
				</p>
			</div>

			<Handle type="source" position={Position.Bottom} className="opacity-0" />
		</div>
	);
};

export default memo(RoadmapNode);
