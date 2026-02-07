import {
	Check,
	CheckCircle,
	Edit3,
	GripVertical,
	Loader2,
	Plus,
	Rocket,
	Target,
	Trash2,
	X,
} from "lucide-react";
import type React from "react";
import { useState } from "react";
import { useRoadmapStore } from "../../stores/useRoadmapStore";

const steps = [
	{ id: 1, label: "Analysis" },
	{ id: 2, label: "Design" },
	{ id: 3, label: "Planning" },
	{ id: 4, label: "Ready" },
];

interface TransitionViewProps {
	onApprove?: (modifiedMilestones?: { id: string; label: string; is_new?: boolean }[]) => void;
}

const TransitionView: React.FC<TransitionViewProps> = ({ onApprove }) => {
	const {
		streamingGoal,
		streamingStatus,
		streamingStep,
		streamingMilestones,
		streamingActions,
		isAwaitingApproval,
		setStreamingMilestones,
	} = useRoadmapStore();

	const [isEditing, setIsEditing] = useState(false);
	const [editedMilestones, setEditedMilestones] = useState<
		{ id: string; label: string; status: "pending" | "generating" | "done" }[]
	>([]);

	const getActionsForMilestone = (milestoneId: string) =>
		streamingActions.filter((a) => a.milestoneId === milestoneId);

	const hasStreamingData = streamingGoal || streamingMilestones.length > 0;

	// Start editing mode
	const handleStartEdit = () => {
		setEditedMilestones([...streamingMilestones]);
		setIsEditing(true);
	};

	// Cancel editing
	const handleCancelEdit = () => {
		setIsEditing(false);
		setEditedMilestones([]);
	};

	// Save edits and approve
	const handleSaveAndApprove = () => {
		// Update the store with edited milestones
		setStreamingMilestones(editedMilestones);
		setIsEditing(false);
		
		// Convert to API format and send to backend
		const modifiedForApi = editedMilestones.map((m) => ({
			id: m.id,
			label: m.label,
			is_new: m.id.startsWith("new-"),
		}));
		
		onApprove?.(modifiedForApi);
	};

	// Update milestone label
	const handleMilestoneChange = (id: string, newLabel: string) => {
		setEditedMilestones((prev) =>
			prev.map((m) => (m.id === id ? { ...m, label: newLabel } : m)),
		);
	};

	// Remove milestone
	const handleRemoveMilestone = (id: string) => {
		setEditedMilestones((prev) => prev.filter((m) => m.id !== id));
	};

	// Add new milestone
	const handleAddMilestone = () => {
		const newMilestone = {
			id: `new-${Date.now()}`,
			label: "New Milestone",
			status: "done" as const,
		};
		setEditedMilestones((prev) => [...prev, newMilestone]);
	};

	const displayMilestones = isEditing ? editedMilestones : streamingMilestones;

	return (
		<div className="fixed inset-0 z-50 bg-slate-900 flex flex-col items-center justify-center text-white overflow-y-auto py-8">
			<div className="relative mb-8">
				<div className="absolute inset-0 bg-amber-500 blur-3xl opacity-20 animate-pulse" />
				<Target className="w-16 h-16 text-amber-400 animate-pulse" />
			</div>

			<div className="text-center mb-8 w-full max-w-lg px-6">
				<h2 className="text-2xl font-bold mb-6">
					{isEditing
						? "Edit Your Roadmap"
						: isAwaitingApproval
							? "Review Your Roadmap"
							: "Constructing Your Roadmap"}
				</h2>

				{/* Progress Stepper */}
				<div className="flex items-center justify-between relative mb-8">
					<div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-0.5 bg-slate-800 -z-10" />
					<div
						className="absolute left-0 top-1/2 -translate-y-1/2 h-0.5 bg-blue-500 transition-all duration-500 ease-in-out -z-10"
						style={{
							width: `${Math.max(0, (streamingStep - 1) / (steps.length - 1)) * 100}%`,
						}}
					/>

					{steps.map((step) => {
						const isCompleted = streamingStep > step.id;
						const isActive = streamingStep >= step.id;
						const isPaused = (isAwaitingApproval || isEditing) && step.id === 2;

						return (
							<div key={step.id} className="flex flex-col items-center gap-2">
								<div
									className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
										isPaused
											? "bg-amber-500/20 border-amber-500 text-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.5)]"
											: isActive
												? "bg-[#101722] border-blue-500 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
												: "bg-[#101722] border-slate-700 text-slate-600"
									}`}
								>
									{isCompleted && !isPaused ? (
										<Check className="w-4 h-4" />
									) : (
										<span className="text-xs font-bold">{step.id}</span>
									)}
								</div>
								<span
									className={`text-xs font-bold uppercase tracking-wider transition-colors duration-300 ${
										isPaused
											? "text-amber-400"
											: isActive
												? "text-blue-400"
												: "text-slate-600"
									}`}
								>
									{step.label}
								</span>
							</div>
						);
					})}
				</div>

				<p className="text-slate-400 text-sm h-6">
					{isEditing
						? "Drag to reorder, click to edit, or add new milestones"
						: streamingStatus ||
							(hasStreamingData
								? "Building your path to success..."
								: "Analyzing your goals...")}
				</p>
			</div>

			{hasStreamingData && (
				<div className="w-full max-w-lg px-6">
					{streamingGoal && (
						<div className="mb-6 p-4 bg-slate-800/50 rounded-xl border border-amber-500/30">
							<div className="flex items-center gap-3">
								<Target className="w-6 h-6 text-amber-400" />
								<div>
									<p className="text-xs text-amber-400/70 font-medium uppercase tracking-wider">
										Main Goal
									</p>
									<p className="text-white font-semibold">{streamingGoal}</p>
								</div>
							</div>
						</div>
					)}

					<div className="space-y-3">
						{displayMilestones.map((milestone, idx) => (
							<div
								key={milestone.id}
								className={`p-3 rounded-lg border transition-all ${
									isEditing
										? "bg-slate-800/70 border-amber-500/30"
										: milestone.status === "done"
											? "bg-slate-800/50 border-blue-500/30"
											: milestone.status === "generating"
												? "bg-slate-800/70 border-blue-400/50 animate-pulse"
												: "bg-slate-800/30 border-slate-700/30"
								}`}
							>
								<div className="flex items-center gap-3">
									{isEditing ? (
										<>
											<GripVertical className="w-5 h-5 text-slate-500 cursor-grab" />
											<div className="flex-1">
												<p className="text-xs text-slate-400 mb-1">
													Milestone {idx + 1}
												</p>
												<input
													type="text"
													value={milestone.label}
													onChange={(e) =>
														handleMilestoneChange(milestone.id, e.target.value)
													}
													className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-amber-500"
												/>
											</div>
											<button
												type="button"
												onClick={() => handleRemoveMilestone(milestone.id)}
												className="p-2 hover:bg-red-900/30 rounded-lg text-slate-500 hover:text-red-400 transition-colors"
											>
												<Trash2 className="w-4 h-4" />
											</button>
										</>
									) : (
										<>
											{milestone.status === "done" ? (
												<CheckCircle className="w-5 h-5 text-blue-400" />
											) : milestone.status === "generating" ? (
												<Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
											) : (
												<div className="w-5 h-5 rounded-full border-2 border-slate-600" />
											)}
											<div className="flex-1">
												<p className="text-xs text-slate-400">
													Milestone {idx + 1}
												</p>
												<p
													className={`font-medium ${
														milestone.status === "pending"
															? "text-slate-500"
															: "text-white"
													}`}
												>
													{milestone.label}
												</p>
											</div>
										</>
									)}
								</div>

								{!isEditing &&
									getActionsForMilestone(milestone.id).length > 0 && (
										<div className="mt-2 ml-8 space-y-1">
											{getActionsForMilestone(milestone.id).map((action) => (
												<div
													key={action.id}
													className="flex items-center gap-2 text-sm text-emerald-400/80"
												>
													<span>→</span>
													<span>{action.label}</span>
												</div>
											))}
										</div>
									)}
							</div>
						))}

						{/* Add Milestone Button (Edit Mode) */}
						{isEditing && (
							<button
								type="button"
								onClick={handleAddMilestone}
								className="w-full p-3 rounded-lg border-2 border-dashed border-slate-700 hover:border-amber-500/50 text-slate-500 hover:text-amber-400 transition-all flex items-center justify-center gap-2"
							>
								<Plus className="w-4 h-4" />
								<span className="text-sm font-medium">Add Milestone</span>
							</button>
						)}
					</div>
				</div>
			)}

			{/* Action Buttons */}
			{isAwaitingApproval && !isEditing && (
				<div className="mt-8 flex gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
					<button
						type="button"
						onClick={() => onApprove?.()}
						className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl font-bold text-sm uppercase tracking-wider shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-105 transition-all active:scale-95"
					>
						<Rocket className="w-5 h-5" />
						Approve & Continue
					</button>
					<button
						type="button"
						onClick={handleStartEdit}
						className="flex items-center gap-2 px-6 py-4 bg-slate-800 border border-slate-700 text-slate-300 rounded-xl font-medium text-sm hover:bg-slate-700 hover:text-white transition-all"
					>
						<Edit3 className="w-4 h-4" />
						Edit
					</button>
				</div>
			)}

			{/* Edit Mode Buttons */}
			{isEditing && (
				<div className="mt-8 flex gap-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
					<button
						type="button"
						onClick={handleSaveAndApprove}
						disabled={editedMilestones.length === 0}
						className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-amber-600 to-amber-500 text-white rounded-xl font-bold text-sm uppercase tracking-wider shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:scale-105 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						<Check className="w-5 h-5" />
						Save & Continue
					</button>
					<button
						type="button"
						onClick={handleCancelEdit}
						className="flex items-center gap-2 px-6 py-4 bg-slate-800 border border-slate-700 text-slate-300 rounded-xl font-medium text-sm hover:bg-slate-700 hover:text-white transition-all"
					>
						<X className="w-4 h-4" />
						Cancel
					</button>
				</div>
			)}

			{/* Loading dots - Show when not awaiting approval and not editing */}
			{!isAwaitingApproval && !isEditing && (
				<div className="mt-8 flex gap-1">
					{[1, 2, 3, 4, 5].map((i) => (
						<div
							key={i}
							className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"
							style={{ animationDelay: `${i * 0.2}s` }}
						/>
					))}
				</div>
			)}
		</div>
	);
};

export default TransitionView;
