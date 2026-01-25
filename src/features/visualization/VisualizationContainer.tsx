import {
	ChevronDown,
	ChevronUp,
	Download,
	Info,
	Loader2,
	LogOut,
	Swords,
	X,
} from "lucide-react";
import { useMemo, useState } from "react";
import ReactFlow, {
	Background,
	Controls,
	Panel,
	ReactFlowProvider,
} from "reactflow";
import { consultNode } from "../../services/gemini";
import { useAppStore, useAuthStore, useRoadmapStore } from "../../stores";
import { AppState } from "../../types";

import RoadmapNodeComponent from "./components/RoadmapNode";

const nodeTypes = {
	roadmapNode: RoadmapNodeComponent,
};

export function VisualizationContainer() {
	const { setAppState } = useAppStore();
	const {
		roadmap,
		nodes: flowNodes,
		edges: flowEdges,
		onNodesChange,
		onEdgesChange,
		selectedNodeId,
		setSelectedNodeId,
	} = useRoadmapStore();

	const [nodeChatInput, setNodeChatInput] = useState("");
	const [nodeChatResponse, setNodeChatResponse] = useState<string | null>(null);
	const [isNodeChatting, setIsNodeChatting] = useState(false);
	const [isQuestPanelExpanded, setIsQuestPanelExpanded] = useState(false);

	const handleNodeChat = async () => {
		if (!selectedNodeId || !nodeChatInput.trim()) return;

		// Find the full node object since consultNode needs details
		const targetNode = roadmap?.nodes.find((n) => n.id === selectedNodeId);
		if (!targetNode) return;

		setIsNodeChatting(true);
		try {
			const response = await consultNode(targetNode, nodeChatInput);
			setNodeChatResponse(response);
			setNodeChatInput(""); // Clear input
		} catch (e) {
			console.error(e);
			setNodeChatResponse("Tactical comms disrupted. Is the frequency clear?");
		} finally {
			setIsNodeChatting(false);
		}
	};

	const selectedNode = useMemo(() => {
		if (!selectedNodeId || !roadmap) return null;
		return roadmap.nodes.find((n) => n.id === selectedNodeId);
	}, [selectedNodeId, roadmap]);

	if (!roadmap) return null;

	return (
		<div className="flex w-full h-full relative">
			<ReactFlowProvider>
				<div className="flex-1 h-full bg-[#101722]">
					<ReactFlow
						nodes={flowNodes}
						edges={flowEdges}
						onNodesChange={onNodesChange}
						onEdgesChange={onEdgesChange}
						nodeTypes={nodeTypes}
						onNodeClick={(_, node) => setSelectedNodeId(node.id)}
						fitView
					>
						<Background color="#223149" gap={40} className="bg-grid-pattern" />
						<Controls className="bg-slate-800 border-slate-700 fill-white" />

						<Panel
							position="top-left"
							className="bg-[#1a2436]/90 backdrop-blur border border-slate-700 rounded-2xl shadow-2xl max-w-sm m-6 transition-all duration-300 overflow-hidden"
						>
							<div className="p-6">
								<div className="flex items-start justify-between gap-4">
									<div>
										<h3 className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-1">
											Active Quest
										</h3>
										<h2 className="text-xl font-black text-white leading-tight">
											{roadmap.title}
										</h2>
									</div>
									<button
										type="button"
										onClick={() =>
											setIsQuestPanelExpanded(!isQuestPanelExpanded)
										}
										className="p-1 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors"
									>
										{isQuestPanelExpanded ? (
											<ChevronUp className="w-5 h-5" />
										) : (
											<ChevronDown className="w-5 h-5" />
										)}
									</button>
								</div>

								{isQuestPanelExpanded && (
									<div className="mt-4 pt-4 border-t border-slate-700 animate-in slide-in-from-top-2 fade-in">
										<p className="text-xs text-slate-400 leading-relaxed italic">
											{roadmap.summary}
										</p>
									</div>
								)}
							</div>
						</Panel>

						<Panel position="top-right" className="m-6 flex gap-3">
							<button
								type="button"
								className="p-3 bg-slate-800/80 border border-slate-700 rounded-xl hover:bg-slate-700 text-slate-300 transition-colors"
								title="Download Roadmap"
							>
								<Download className="w-5 h-5" />
							</button>
							<button
								type="button"
								className="p-3 bg-slate-800/80 border border-slate-700 rounded-xl hover:bg-slate-700 text-slate-300 transition-colors"
								title="Logout"
								onClick={() => useAuthStore.getState().signOut()}
							>
								<LogOut className="w-5 h-5" />
							</button>
							<button
								type="button"
								onClick={() => setAppState(AppState.DISCOVERY)}
								className="flex items-center gap-2 px-6 py-3 bg-slate-100 text-slate-900 rounded-xl font-black text-xs uppercase tracking-widest shadow-lg hover:bg-white transition-all active:scale-95"
							>
								<X className="w-4 h-4" /> Exit
							</button>
						</Panel>
					</ReactFlow>
				</div>

				{selectedNode && (
					<div className="w-96 bg-[#182334] border-l border-slate-800 shadow-2xl flex flex-col z-10 animate-in slide-in-from-right duration-300">
						<div className="p-8 border-b border-slate-800 bg-[#101722]/50">
							<div className="flex items-center justify-between mb-4">
								<span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">
									Quest Intel
								</span>
								<button
									type="button"
									onClick={() => setSelectedNodeId(null)}
									className="text-slate-500 hover:text-white transition-colors"
								>
									<X className="w-6 h-6" />
								</button>
							</div>
							<h2 className="text-2xl font-black text-white leading-tight mb-2">
								{selectedNode.label}
							</h2>
							<div className="flex gap-2">
								<span className="px-2 py-1 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400 text-[10px] font-black">
									+150 XP
								</span>
								<span className="px-2 py-1 rounded bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[10px] font-black">
									Main Story
								</span>
							</div>
						</div>

						<div className="flex-1 overflow-y-auto p-8 space-y-8">
							{selectedNode.is_assumed && (
								<div className="bg-purple-900/20 border border-purple-500/30 rounded-2xl p-4 flex gap-3">
									<Info className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
									<p className="text-xs text-purple-200 leading-relaxed italic">
										Oracle Suggestion: This step was divined to ensure your path
										remains unbroken.
									</p>
								</div>
							)}

							<div className="space-y-4">
								<h4 className="font-black text-[10px] text-slate-500 uppercase tracking-widest flex items-center gap-2">
									<div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]"></div>{" "}
									Action Items
								</h4>
								<ul className="space-y-3">
									{selectedNode.details.map((detail, i) => (
										<li
											key={`${i}-${detail}`}
											className="flex gap-3 text-sm text-slate-300 p-3 rounded-xl bg-slate-900/50 border border-slate-800/50 group hover:border-blue-500/30 transition-colors"
										>
											<input
												type="checkbox"
												className="mt-1 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500/20"
											/>
											<span className="leading-relaxed">{detail}</span>
										</li>
									))}
								</ul>
							</div>
						</div>

						<div className="bg-[#101722] border-t border-slate-800 flex flex-col h-64">
							<div className="flex-1 overflow-y-auto p-4 space-y-3">
								{/* Chat History Placeholder - For now, just ephemeral chat */}
								<div className="flex gap-3">
									<div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
										<Swords className="w-4 h-4 text-white" />
									</div>
									<div className="bg-slate-800 rounded-2xl rounded-tl-none p-3 text-sm text-slate-300">
										<p>
											I am ready to advise on{" "}
											<span className="text-blue-400 font-bold">
												{selectedNode.label}
											</span>
											. What is your query?
										</p>
									</div>
								</div>
							</div>
							<div className="p-4 border-t border-slate-800 bg-[#182334]">
								<div className="relative">
									<input
										type="text"
										value={nodeChatInput}
										onChange={(e) => setNodeChatInput(e.target.value)}
										placeholder="Ask for tactics..."
										className="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-blue-500 pr-12 disabled:opacity-50"
										disabled={isNodeChatting}
										onKeyDown={(e) => {
											if (e.key === "Enter") {
												handleNodeChat();
											}
										}}
									/>
									<button
										type="button"
										onClick={handleNodeChat}
										disabled={isNodeChatting || !nodeChatInput.trim()}
										className="absolute right-2 top-2 p-1.5 bg-blue-600 rounded-lg text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										{isNodeChatting ? (
											<Loader2 className="w-4 h-4 animate-spin" />
										) : (
											<Swords className="w-4 h-4" />
										)}
									</button>
								</div>
								{nodeChatResponse && (
									<div className="mt-4 p-3 bg-blue-900/20 border border-blue-500/30 rounded-xl">
										<p className="text-xs text-blue-200 leading-relaxed italic animate-in fade-in slide-in-from-bottom-2">
											"{nodeChatResponse}"
										</p>
									</div>
								)}
							</div>
						</div>

						<div className="p-8 bg-[#101722] border-t border-slate-800">
							<button
								type="button"
								className="w-full py-4 bg-blue-600 text-white rounded-xl font-black text-xs uppercase tracking-[0.2em] shadow-xl hover:bg-blue-500 active:scale-95 transition-all"
							>
								Mark Quest as Accomplished
							</button>
						</div>
					</div>
				)}
			</ReactFlowProvider>
		</div>
	);
}
