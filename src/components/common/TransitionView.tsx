import { Check, CheckCircle, Loader2, Target } from "lucide-react";
import type React from "react";
import { useRoadmapStore } from "../../stores/useRoadmapStore";

const steps = [
	{ id: 1, label: "Analysis" },
	{ id: 2, label: "Design" },
	{ id: 3, label: "Planning" },
	{ id: 4, label: "Ready" },
];

const TransitionView: React.FC = () => {
	const {
		streamingGoal,
		streamingStatus,
		streamingStep,
		streamingMilestones,
		streamingActions,
	} = useRoadmapStore();

	const getActionsForMilestone = (milestoneId: string) =>
		streamingActions.filter((a) => a.milestoneId === milestoneId);

	const hasStreamingData = streamingGoal || streamingMilestones.length > 0;

	return (
		<div className="fixed inset-0 z-50 bg-slate-900 flex flex-col items-center justify-center text-white">
			<div className="relative mb-8">
				<div className="absolute inset-0 bg-amber-500 blur-3xl opacity-20 animate-pulse" />
				<Target className="w-16 h-16 text-amber-400 animate-pulse" />
			</div>

			<div className="text-center mb-8 w-full max-w-lg px-6">
				<h2 className="text-2xl font-bold mb-6">Constructing Your Roadmap</h2>

				{/* Progress Stepper */}
				<div className="flex items-center justify-between relative mb-8">
					{/* Connecting Line */}
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

						return (
							<div key={step.id} className="flex flex-col items-center gap-2">
								<div
									className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 ${
										isActive
											? "bg-[#101722] border-blue-500 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.5)]"
											: "bg-[#101722] border-slate-700 text-slate-600"
									}`}
								>
									{isCompleted ? (
										<Check className="w-4 h-4" />
									) : (
										<span className="text-xs font-bold">{step.id}</span>
									)}
								</div>
								<span
									className={`text-xs font-bold uppercase tracking-wider transition-colors duration-300 ${
										isActive ? "text-blue-400" : "text-slate-600"
									}`}
								>
									{step.label}
								</span>
							</div>
						);
					})}
				</div>

				<p className="text-slate-400 text-sm h-6">
					{streamingStatus ||
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

			<div className="mt-8 flex gap-1">
				{[1, 2, 3, 4, 5].map((i) => (
					<div
						key={i}
						className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"
						style={{ animationDelay: `${i * 0.2}s` }}
					/>
				))}
			</div>
		</div>
	);
};

export default TransitionView;
