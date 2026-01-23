import { Sparkles, Sword, Trophy } from "lucide-react";
import { memo } from "react";
import { Handle, Position } from "reactflow";

const RoadmapNode = ({ data }: any) => {
	const isAssumed = data.is_assumed;
	const isMilestone = data.type === "milestone";
	const isTask = data.type === "task";

	return (
		<div className="group flex flex-col items-center gap-3">
			<Handle type="target" position={Position.Top} className="opacity-0" />

			<div
				className={`relative flex items-center justify-center transition-all duration-300 group-hover:scale-110 ${
					isMilestone ? "w-20 h-20" : isTask ? "w-10 h-10" : "w-16 h-16"
				}`}
			>
				{/* Glow Ring */}
				<div
					className={`absolute inset-0 rounded-full blur-md opacity-40 transition-opacity group-hover:opacity-80 ${
						isAssumed
							? "bg-purple-600"
							: isTask
								? "bg-emerald-600"
								: "bg-blue-600"
					}`}
				/>

				{/* Main Circle */}
				<div
					className={`relative w-full h-full rounded-full border-[3px] flex items-center justify-center bg-[#1a2436] shadow-2xl ${
						isAssumed
							? "border-purple-500/50 border-dashed"
							: isTask
								? "border-emerald-500"
								: "border-blue-500"
					}`}
				>
					{isMilestone ? (
						<Trophy
							className={`w-8 h-8 ${isAssumed ? "text-purple-400" : "text-blue-400"}`}
						/>
					) : isTask ? (
						<div
							className={`w-3 h-3 rounded-full ${isAssumed ? "bg-purple-400" : "bg-emerald-400"}`}
						/>
					) : (
						<Sword
							className={`w-6 h-6 ${isAssumed ? "text-purple-400/70" : "text-blue-400/70"}`}
						/>
					)}

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
				className={`px-4 py-2 rounded-xl border bg-[#101722]/90 backdrop-blur-sm shadow-xl transition-all group-hover:border-blue-500/50 ${
					isAssumed
						? "border-purple-900/50 text-purple-200"
						: isTask
							? "border-emerald-900/50 text-emerald-100"
							: "border-slate-800 text-white"
				}`}
			>
				{!isTask && (
					<p className="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 text-center mb-0.5">
						{isMilestone ? "Milestone" : "Step"}
					</p>
				)}
				<p
					className={`font-bold whitespace-nowrap ${isTask ? "text-[10px]" : "text-xs"}`}
				>
					{data.label}
				</p>
			</div>

			<Handle type="source" position={Position.Bottom} className="opacity-0" />
		</div>
	);
};

export default memo(RoadmapNode);
