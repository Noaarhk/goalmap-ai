import {
	Info,
	Loader2,
	LogOut,
	Swords,
	X,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useAppStore, useAuthStore, useRoadmapStore } from "../../stores";
import { AppState } from "../../types";
import type { RoadmapNode } from "../../types";

import { CheckInPanel } from "./components/CheckInPanel";
import { GoalHero } from "./components/GoalHero";
import { MilestoneSection } from "./components/MilestoneSection";

const isValidUUID = (id: string): boolean => {
	const uuidRegex =
		/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
	return uuidRegex.test(id);
};

export function VisualizationContainer() {
	const { setAppState } = useAppStore();
	const {
		roadmap,
		selectedNodeId,
		setSelectedNodeId,
		syncFromServer,
	} = useRoadmapStore();

	const [isSyncing, setIsSyncing] = useState(false);
	const [nodeChatInput, setNodeChatInput] = useState("");
	const [nodeChatResponse, setNodeChatResponse] = useState<string | null>(null);
	const [isNodeChatting, setIsNodeChatting] = useState(false);
	const hasSynced = useRef(false);

	useEffect(() => {
		const roadmapId = roadmap?.id;
		if (roadmapId && isValidUUID(roadmapId) && !hasSynced.current) {
			hasSynced.current = true;
			setIsSyncing(true);
			syncFromServer(roadmapId).finally(() => setIsSyncing(false));
		}
	}, [roadmap?.id, syncFromServer]);

	const handleNodeChat = async () => {
		if (!selectedNodeId || !nodeChatInput.trim()) return;
		const targetNode = roadmap?.nodes.find((n) => n.id === selectedNodeId);
		if (!targetNode) return;

		setIsNodeChatting(true);
		try {
			setNodeChatResponse("Consult API not yet implemented.");
			setNodeChatInput("");
		} catch (e) {
			console.error(e);
			setNodeChatResponse("Something went wrong. Try again.");
		} finally {
			setIsNodeChatting(false);
		}
	};

	// Derive hierarchy from flat node list
	const { goal, milestones, tasksByMilestone, orphanTasks } = useMemo(() => {
		if (!roadmap) return { goal: null, milestones: [], tasksByMilestone: new Map(), orphanTasks: [] };

		const nodes = roadmap.nodes;
		const edges = roadmap.edges;

		// Build a parentId lookup from edges as fallback
		const edgeParentMap = new Map<string, string>();
		for (const edge of edges) {
			edgeParentMap.set(edge.target, edge.source);
		}

		const goalNode = nodes.find((n) => n.type === "goal") || null;
		const milestoneNodes = nodes
			.filter((n) => n.type === "milestone")
			.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

		const taskMap = new Map<string, RoadmapNode[]>();
		const orphans: RoadmapNode[] = [];

		for (const node of nodes) {
			if (node.type !== "task") continue;
			// Use parentId if available, otherwise derive from edges
			const parentId = node.parentId || edgeParentMap.get(node.id);
			if (parentId) {
				if (!taskMap.has(parentId)) {
					taskMap.set(parentId, []);
				}
				taskMap.get(parentId)!.push(node);
			} else {
				orphans.push(node);
			}
		}

		// Sort tasks within each milestone by order
		for (const [, tasks] of taskMap) {
			tasks.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
		}

		return {
			goal: goalNode,
			milestones: milestoneNodes,
			tasksByMilestone: taskMap,
			orphanTasks: orphans,
		};
	}, [roadmap]);

	const selectedNode = useMemo(() => {
		if (!selectedNodeId || !roadmap) return null;
		return roadmap.nodes.find((n) => n.id === selectedNodeId) ?? null;
	}, [selectedNodeId, roadmap]);

	// Compute overall progress
	const totalProgress = useMemo(() => {
		if (!roadmap) return 0;
		const allNodes = roadmap.nodes.filter((n) => n.type !== "goal");
		if (allNodes.length === 0) return 0;
		const sum = allNodes.reduce((acc, n) => acc + (n.progress ?? 0), 0);
		return Math.round(sum / allNodes.length);
	}, [roadmap]);

	if (!roadmap) return null;

	return (
		<div className="flex w-full h-screen relative">
			{/* Main scrollable content */}
			<div className="flex-1 h-full overflow-y-auto bg-[#101722]">
				{/* Top nav bar */}
				<div className="sticky top-0 z-20 bg-[#101722]/90 backdrop-blur-md border-b border-slate-800/50">
					<div className="max-w-4xl mx-auto px-6 py-3 flex items-center justify-between">
						<div className="flex items-center gap-3">
							<h2 className="text-sm font-bold text-white truncate max-w-[300px]">
								{roadmap.title}
							</h2>
							{isSyncing && (
								<div className="flex items-center gap-1.5 text-[10px] text-emerald-400">
									<Loader2 className="w-3 h-3 animate-spin" />
									<span>Syncing</span>
								</div>
							)}
						</div>
						<div className="flex items-center gap-2">
							<button
								type="button"
								onClick={() => useAuthStore.getState().signOut()}
								className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700/50 hover:bg-red-900/20 hover:border-red-900/50 text-slate-400 hover:text-red-400 transition-all text-xs"
							>
								<LogOut className="w-3.5 h-3.5" />
								Log Out
							</button>
							<button
								type="button"
								onClick={() => setAppState(AppState.DISCOVERY)}
								className="flex items-center gap-1.5 px-4 py-2 bg-slate-100 text-slate-900 rounded-lg font-bold text-xs hover:bg-white transition-all active:scale-95"
							>
								<X className="w-3.5 h-3.5" />
								Exit
							</button>
						</div>
					</div>
				</div>

				{/* Timeline content */}
				<div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
					{/* Goal hero */}
					{goal && (
						<GoalHero
							goal={goal}
							totalProgress={totalProgress}
							milestoneCount={milestones.length}
							taskCount={roadmap.nodes.filter((n) => n.type === "task").length}
							isSyncing={isSyncing}
						/>
					)}

					{/* Timeline: Milestones + Tasks */}
					{milestones.length > 0 && (
						<div className="pt-2">
							{milestones.map((milestone, idx) => (
								<MilestoneSection
									key={milestone.id}
									milestone={milestone}
									tasks={tasksByMilestone.get(milestone.id) ?? []}
									isLast={idx === milestones.length - 1}
									selectedNodeId={selectedNodeId}
									onNodeSelect={setSelectedNodeId}
								/>
							))}
						</div>
					)}

					{/* Orphan tasks (tasks without a milestone parent) */}
					{orphanTasks.length > 0 && (
						<div className="mt-6">
							<h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
								Other Tasks
							</h3>
							<div className="grid grid-cols-1 md:grid-cols-2 gap-3">
								{orphanTasks.map((task) => (
									<button
										key={task.id}
										type="button"
										onClick={() => setSelectedNodeId(task.id)}
										className={`text-left p-4 rounded-xl border transition-all ${
											selectedNodeId === task.id
												? "border-blue-500/60 bg-blue-500/5"
												: "border-slate-700/50 bg-[#1a2436] hover:border-slate-600"
										}`}
									>
										<p className="text-sm font-semibold text-white">
											{task.label}
										</p>
										{task.details && (
											<p className="text-xs text-slate-500 mt-1 line-clamp-2">
												{task.details}
											</p>
										)}
									</button>
								))}
							</div>
						</div>
					)}

					{/* Check-in panel */}
					<div className="pb-8">
						{isValidUUID(roadmap.id) ? (
							<CheckInPanel
								roadmapId={roadmap.id}
								nodes={roadmap.nodes}
								onUpdatesConfirmed={(updatedNodeIds) => {
									console.log("Updates confirmed for nodes:", updatedNodeIds);
									useRoadmapStore.getState().refreshNodesFromRoadmap();
								}}
							/>
						) : (
							<div className="bg-[#1a2436]/95 border border-slate-700 p-4 rounded-2xl text-center">
								<p className="text-xs text-slate-500">
									Check-in not available for this roadmap. Generate a new
									roadmap to enable progress tracking.
								</p>
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Detail side panel */}
			{selectedNode && (
				<div className="w-[400px] shrink-0 bg-[#182334] border-l border-slate-800 shadow-2xl flex flex-col z-10 animate-in slide-in-from-right duration-300">
					{/* Panel header */}
					<div className="p-6 border-b border-slate-800 bg-[#101722]/50">
						<div className="flex items-center justify-between mb-3">
							<span
								className={`text-[10px] font-bold uppercase tracking-widest ${
									selectedNode.type === "goal"
										? "text-amber-400"
										: selectedNode.type === "milestone"
											? "text-blue-400"
											: "text-emerald-400"
								}`}
							>
								{selectedNode.type === "goal"
									? "Goal Details"
									: selectedNode.type === "milestone"
										? "Milestone Details"
										: "Task Details"}
							</span>
							<button
								type="button"
								onClick={() => setSelectedNodeId(null)}
								className="p-1 rounded-lg text-slate-500 hover:text-white hover:bg-slate-700/50 transition-colors"
							>
								<X className="w-5 h-5" />
							</button>
						</div>
						<h2 className="text-xl font-bold text-white leading-tight">
							{selectedNode.label}
						</h2>
					</div>

					{/* Panel body */}
					<div className="flex-1 overflow-y-auto p-6 space-y-5">
						{selectedNode.isAssumed && (
							<div className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-3.5 flex gap-3">
								<Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
								<p className="text-xs text-purple-200 leading-relaxed">
									This step was AI-generated to keep your roadmap well-structured.
								</p>
							</div>
						)}

						{/* Planning & Progress */}
						<div className="space-y-4 p-4 bg-slate-900/30 rounded-xl border border-slate-800">
							<h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
								Progress
							</h4>

							<div className="grid grid-cols-2 gap-3">
								<div className="space-y-1">
									<span className="text-[9px] font-bold text-slate-600 uppercase">
										Start
									</span>
									<p className="text-xs text-slate-300">
										{selectedNode.startDate || "Not set"}
									</p>
								</div>
								<div className="space-y-1">
									<span className="text-[9px] font-bold text-slate-600 uppercase">
										End
									</span>
									<p className="text-xs text-slate-300">
										{selectedNode.endDate || "Not set"}
									</p>
								</div>
							</div>

							<div className="space-y-2">
								<div className="flex justify-between">
									<span className="text-[9px] font-bold text-slate-600 uppercase">
										Progress
									</span>
									<span className="text-xs font-bold text-blue-400">
										{selectedNode.progress || 0}%
									</span>
								</div>
								<div className="h-2 bg-slate-800 rounded-full overflow-hidden">
									<div
										className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full transition-all"
										style={{
											width: `${selectedNode.progress || 0}%`,
										}}
									/>
								</div>
							</div>

							{selectedNode.completionCriteria && (
								<div className="space-y-1">
									<span className="text-[9px] font-bold text-slate-600 uppercase">
										Success Criteria
									</span>
									<p className="text-xs text-emerald-300 italic">
										{selectedNode.completionCriteria}
									</p>
								</div>
							)}
						</div>

						{/* Child Nodes */}
						{(selectedNode.type === "goal" ||
							selectedNode.type === "milestone") && (
							<div className="space-y-3">
								<h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
									<div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
									{selectedNode.type === "goal"
										? "Milestones & Tasks"
										: "Tasks"}
								</h4>
								<ul className="space-y-1.5">
									{roadmap?.nodes
										.filter((n) => n.parentId === selectedNode.id)
										.map((child) => (
											<li key={child.id}>
												<button
													type="button"
													className="flex items-center gap-3 w-full text-left text-sm text-slate-300 p-3 rounded-lg bg-slate-900/50 border border-slate-800/50 hover:border-slate-600 transition-colors"
													onClick={() =>
														setSelectedNodeId(child.id)
													}
												>
													<div
														className={`w-2 h-2 rounded-full shrink-0 ${
															child.type === "milestone"
																? "bg-blue-500"
																: "bg-emerald-500"
														}`}
													/>
													<span className="flex-1 truncate">
														{child.label}
													</span>
													<span className="text-[10px] text-slate-500 tabular-nums">
														{child.progress || 0}%
													</span>
												</button>
											</li>
										))}
									{!roadmap?.nodes.some(
										(n) => n.parentId === selectedNode.id,
									) && (
										<p className="text-xs text-slate-600 italic text-center py-2">
											No child nodes
										</p>
									)}
								</ul>
							</div>
						)}

						{/* Details */}
						{selectedNode.details && (
							<div className="space-y-3">
								<h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-2">
									<div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
									Details
								</h4>
								<p className="text-sm text-slate-300 p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/50 leading-relaxed">
									{selectedNode.details}
								</p>
							</div>
						)}
					</div>

					{/* Chat section */}
					<div className="bg-[#101722] border-t border-slate-800 flex flex-col h-52">
						<div className="flex-1 overflow-y-auto p-4 space-y-3">
							<div className="flex gap-3">
								<div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
									<Swords className="w-3.5 h-3.5 text-white" />
								</div>
								<div className="bg-slate-800 rounded-2xl rounded-tl-none p-3 text-sm text-slate-300">
									<p>
										Ask me about{" "}
										<span className="text-blue-400 font-semibold">
											{selectedNode.label}
										</span>
									</p>
								</div>
							</div>
							{nodeChatResponse && (
								<div className="ml-10 p-3 bg-blue-900/20 border border-blue-500/30 rounded-xl">
									<p className="text-xs text-blue-200 leading-relaxed italic">
										"{nodeChatResponse}"
									</p>
								</div>
							)}
						</div>
						<div className="p-3 border-t border-slate-800 bg-[#182334]">
							<div className="relative">
								<input
									type="text"
									value={nodeChatInput}
									onChange={(e) => setNodeChatInput(e.target.value)}
									placeholder="Ask a question..."
									className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500 pr-10 disabled:opacity-50"
									disabled={isNodeChatting}
									onKeyDown={(e) => {
										if (e.key === "Enter") handleNodeChat();
									}}
								/>
								<button
									type="button"
									onClick={handleNodeChat}
									disabled={isNodeChatting || !nodeChatInput.trim()}
									className="absolute right-1.5 top-1.5 p-1.5 bg-blue-600 rounded-md text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
								>
									{isNodeChatting ? (
										<Loader2 className="w-3.5 h-3.5 animate-spin" />
									) : (
										<Swords className="w-3.5 h-3.5" />
									)}
								</button>
							</div>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
