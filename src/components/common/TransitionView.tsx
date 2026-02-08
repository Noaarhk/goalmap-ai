import {
	ArrowLeft,
	Calendar,
	Check,
	CheckCircle,
	ClipboardCheck,
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

type ReviewPhase = "structure" | "schedule";

interface ModifiedMilestone {
	id: string;
	label: string;
	start_date?: string;
	end_date?: string;
	completion_criteria?: string;
	is_new?: boolean;
}

interface TransitionViewProps {
	onApprove?: (modifiedMilestones?: ModifiedMilestone[]) => void;
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
		setStreamingStep,
		setStreamingStatus,
	} = useRoadmapStore();

	// Phase tracking for 2-step approval
	const [reviewPhase, setReviewPhase] = useState<ReviewPhase>("structure");
	const [isEditing, setIsEditing] = useState(false);

	// Structure editing state (labels + add/remove)
	const [editedMilestones, setEditedMilestones] = useState<
		{ id: string; label: string; status: "pending" | "generating" | "done" }[]
	>([]);

	// Schedule editing state (dates + criteria, pre-filled from LLM)
	const [scheduledMilestones, setScheduledMilestones] = useState<
		{ id: string; label: string; startDate: string; endDate: string; completionCriteria: string; isNew: boolean }[]
	>([]);

	const getActionsForMilestone = (milestoneId: string) =>
		streamingActions.filter((a) => a.milestoneId === milestoneId);

	const hasStreamingData = streamingGoal || streamingMilestones.length > 0;

	// --- Structure Phase Handlers ---

	const handleStartEdit = () => {
		setEditedMilestones(
			streamingMilestones.map((m) => ({ id: m.id, label: m.label, status: m.status })),
		);
		setIsEditing(true);
	};

	const handleCancelEdit = () => {
		setIsEditing(false);
		setEditedMilestones([]);
	};

	const handleSaveStructure = () => {
		// Apply label edits to streaming milestones (preserve dates/criteria from LLM)
		const updatedMilestones = editedMilestones.map((edited) => {
			const original = streamingMilestones.find((m) => m.id === edited.id);
			return {
				...edited,
				startDate: original?.startDate,
				endDate: original?.endDate,
				completionCriteria: original?.completionCriteria,
			};
		});
		setStreamingMilestones(updatedMilestones);
		setIsEditing(false);
		setEditedMilestones([]);
	};

	const handleMilestoneChange = (id: string, newLabel: string) => {
		setEditedMilestones((prev) =>
			prev.map((m) => (m.id === id ? { ...m, label: newLabel } : m)),
		);
	};

	const handleRemoveMilestone = (id: string) => {
		setEditedMilestones((prev) => prev.filter((m) => m.id !== id));
	};

	const handleAddMilestone = () => {
		setEditedMilestones((prev) => [
			...prev,
			{ id: `new-${Date.now()}`, label: "New Milestone", status: "done" as const },
		]);
	};

	// --- Phase Transition: Structure → Schedule ---

	const handleApproveStructure = () => {
		setScheduledMilestones(
			streamingMilestones.map((m) => ({
				id: m.id,
				label: m.label,
				startDate: m.startDate ?? "",
				endDate: m.endDate ?? "",
				completionCriteria: m.completionCriteria ?? "",
				isNew: m.id.startsWith("new-"),
			})),
		);
		setReviewPhase("schedule");
		setStreamingStep(3);
		setStreamingStatus("Set timeline and completion criteria");
	};

	// --- Schedule Phase Handlers ---

	const handleScheduleFieldChange = (id: string, field: string, value: string) => {
		setScheduledMilestones((prev) =>
			prev.map((m) => (m.id === id ? { ...m, [field]: value } : m)),
		);
	};

	const handleBackToStructure = () => {
		setReviewPhase("structure");
		setStreamingStep(2);
		setStreamingStatus("Review your roadmap structure");
	};

	const handleConfirmSchedule = () => {
		const modifiedForApi: ModifiedMilestone[] = scheduledMilestones.map((m) => ({
			id: m.id,
			label: m.label,
			start_date: m.startDate || undefined,
			end_date: m.endDate || undefined,
			completion_criteria: m.completionCriteria || undefined,
			is_new: m.isNew,
		}));
		onApprove?.(modifiedForApi);
	};

	// --- Determine display state ---

	const displayMilestones = isEditing ? editedMilestones : streamingMilestones;

	const heading = (() => {
		if (isEditing) return "Edit Milestones";
		if (isAwaitingApproval && reviewPhase === "schedule") return "Set Timeline & Criteria";
		if (isAwaitingApproval) return "Review Your Roadmap";
		return "Constructing Your Roadmap";
	})();

	const subtitle = (() => {
		if (isEditing) return "Rename, reorder, add or remove milestones";
		if (isAwaitingApproval && reviewPhase === "schedule")
			return "Set dates and define what 'done' looks like for each milestone";
		return (
			streamingStatus ||
			(hasStreamingData ? "Building your path to success..." : "Analyzing your goals...")
		);
	})();

	return (
		<div className="fixed inset-0 z-50 bg-slate-900 flex flex-col items-center justify-center text-white overflow-y-auto py-8">
			<div className="relative mb-8">
				<div className="absolute inset-0 bg-amber-500 blur-3xl opacity-20 animate-pulse" />
				<Target className="w-16 h-16 text-amber-400 animate-pulse" />
			</div>

			<div className="text-center mb-8 w-full max-w-lg px-6">
				<h2 className="text-2xl font-bold mb-6">{heading}</h2>

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
						const isPaused =
							(isAwaitingApproval || isEditing) &&
							((reviewPhase === "structure" && step.id === 2) ||
								(reviewPhase === "schedule" && step.id === 3));

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

				<p className="text-slate-400 text-sm h-6">{subtitle}</p>
			</div>

			{/* ============================================ */}
			{/* PHASE: Structure Review / Edit (Step 2)      */}
			{/* ============================================ */}
			{hasStreamingData && reviewPhase === "structure" && (
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
											<GripVertical className="w-5 h-5 text-slate-500 cursor-grab flex-shrink-0" />
											<div className="flex-1 space-y-2">
												<p className="text-xs text-slate-400">
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
												className="p-2 hover:bg-red-900/30 rounded-lg text-slate-500 hover:text-red-400 transition-colors flex-shrink-0"
											>
												<Trash2 className="w-4 h-4" />
											</button>
										</>
									) : (
										<>
											{milestone.status === "done" ? (
												<CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
											) : milestone.status === "generating" ? (
												<Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
											) : (
												<div className="w-5 h-5 rounded-full border-2 border-slate-600 flex-shrink-0" />
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

			{/* ============================================ */}
			{/* PHASE: Schedule & Criteria Review (Step 3)   */}
			{/* ============================================ */}
			{hasStreamingData && reviewPhase === "schedule" && isAwaitingApproval && (
				<div className="w-full max-w-lg px-6">
					<div className="space-y-4">
						{scheduledMilestones.map((milestone, idx) => (
							<div
								key={milestone.id}
								className="p-4 rounded-lg border border-blue-500/20 bg-slate-800/50 space-y-3"
							>
								<div className="flex items-center gap-2">
									<span className="text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">
										{idx + 1}
									</span>
									<p className="text-sm font-semibold text-white">
										{milestone.label}
									</p>
								</div>

								{/* Date range */}
								<div className="flex items-center gap-2">
									<Calendar className="w-4 h-4 text-slate-500 flex-shrink-0" />
									<input
										type="date"
										value={milestone.startDate}
										onChange={(e) =>
											handleScheduleFieldChange(milestone.id, "startDate", e.target.value)
										}
										className="flex-1 bg-slate-900/50 border border-slate-600 rounded-lg px-2.5 py-1.5 text-white text-xs focus:outline-none focus:border-blue-500"
									/>
									<span className="text-xs text-slate-500 font-medium">→</span>
									<input
										type="date"
										value={milestone.endDate}
										onChange={(e) =>
											handleScheduleFieldChange(milestone.id, "endDate", e.target.value)
										}
										className="flex-1 bg-slate-900/50 border border-slate-600 rounded-lg px-2.5 py-1.5 text-white text-xs focus:outline-none focus:border-blue-500"
									/>
								</div>

								{/* Completion criteria */}
								<div className="flex items-start gap-2">
									<ClipboardCheck className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1.5" />
									<input
										type="text"
										value={milestone.completionCriteria}
										onChange={(e) =>
											handleScheduleFieldChange(milestone.id, "completionCriteria", e.target.value)
										}
										placeholder="How do you know this milestone is done?"
										className="flex-1 bg-slate-900/50 border border-slate-600 rounded-lg px-2.5 py-1.5 text-white text-xs focus:outline-none focus:border-blue-500 placeholder:text-slate-600"
									/>
								</div>
							</div>
						))}
					</div>
				</div>
			)}

			{/* ============================================ */}
			{/* ACTION STREAMING PHASE (step 3 running)      */}
			{/* ============================================ */}
			{hasStreamingData && reviewPhase === "schedule" && !isAwaitingApproval && (
				<div className="w-full max-w-lg px-6">
					<div className="space-y-3">
						{streamingMilestones.map((milestone, idx) => (
							<div
								key={milestone.id}
								className={`p-3 rounded-lg border transition-all ${
									milestone.status === "done"
										? "bg-slate-800/50 border-blue-500/30"
										: milestone.status === "generating"
											? "bg-slate-800/70 border-blue-400/50 animate-pulse"
											: "bg-slate-800/30 border-slate-700/30"
								}`}
							>
								<div className="flex items-center gap-3">
									{milestone.status === "done" ? (
										<CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0" />
									) : milestone.status === "generating" ? (
										<Loader2 className="w-5 h-5 text-blue-400 animate-spin flex-shrink-0" />
									) : (
										<div className="w-5 h-5 rounded-full border-2 border-slate-600 flex-shrink-0" />
									)}
									<div className="flex-1">
										<p className="text-xs text-slate-400">Milestone {idx + 1}</p>
										<p className="font-medium text-white">{milestone.label}</p>
									</div>
								</div>

								{getActionsForMilestone(milestone.id).length > 0 && (
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
					</div>
				</div>
			)}

			{/* ============================================ */}
			{/* BUTTONS                                      */}
			{/* ============================================ */}

			{/* Structure Review Buttons */}
			{isAwaitingApproval && reviewPhase === "structure" && !isEditing && (
				<div className="mt-8 flex gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
					<button
						type="button"
						onClick={handleApproveStructure}
						className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl font-bold text-sm uppercase tracking-wider shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 hover:scale-105 transition-all active:scale-95"
					>
						<Rocket className="w-5 h-5" />
						Approve & Set Schedule
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

			{/* Structure Edit Buttons */}
			{isEditing && (
				<div className="mt-8 flex gap-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
					<button
						type="button"
						onClick={handleSaveStructure}
						disabled={editedMilestones.length === 0}
						className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-amber-600 to-amber-500 text-white rounded-xl font-bold text-sm uppercase tracking-wider shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:scale-105 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						<Check className="w-5 h-5" />
						Save
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

			{/* Schedule Review Buttons */}
			{isAwaitingApproval && reviewPhase === "schedule" && (
				<div className="mt-8 flex gap-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
					<button
						type="button"
						onClick={handleConfirmSchedule}
						className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl font-bold text-sm uppercase tracking-wider shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-105 transition-all active:scale-95"
					>
						<Rocket className="w-5 h-5" />
						Confirm & Generate
					</button>
					<button
						type="button"
						onClick={handleBackToStructure}
						className="flex items-center gap-2 px-6 py-4 bg-slate-800 border border-slate-700 text-slate-300 rounded-xl font-medium text-sm hover:bg-slate-700 hover:text-white transition-all"
					>
						<ArrowLeft className="w-4 h-4" />
						Back
					</button>
				</div>
			)}

			{/* Loading dots */}
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
