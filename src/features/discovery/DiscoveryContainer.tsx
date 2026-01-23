import { History, Swords } from "lucide-react";
import { useMemo, useState } from "react";
import type { Edge, Node } from "reactflow";
import ScoreGauge from "../../components/common/ScoreGauge";
import { apiClient } from "../../services/apiClient";
import {
	useAppStore,
	useBlueprintStore,
	useChatStore,
	useRoadmapStore,
} from "../../stores";
import {
	AppState,
	type Message,
	type RoadmapData,
	type RoadmapNode,
} from "../../types";
import BlueprintPreview from "./components/BlueprintPreview";
import ChatPanel from "./components/ChatPanel";

export function DiscoveryContainer() {
	const { setAppState } = useAppStore();
	const { messages, addMessage, setMessages } = useChatStore();
	const {
		blueprint,
		updateBlueprint,
		isChatLoading,
		setIsChatLoading,
		isBlueprintLoading,
		setIsBlueprintLoading,
	} = useBlueprintStore();
	const {
		history: roadmapHistory,
		setRoadmap,
		loadRoadmap,
		setNodes: setFlowNodes,
		setEdges: setFlowEdges,
	} = useRoadmapStore();

	const [showHistory, setShowHistory] = useState(false);

	const infoScore = useMemo(() => {
		if (!blueprint.fieldScores) {
			const fields = ["goal", "why", "timeline", "obstacles", "resources"];
			const filledCount = fields.filter(
				(f) => !!(blueprint as Record<string, any>)[f],
			).length;
			return Math.min(filledCount * 4, 20);
		}
		const scores = Object.values(blueprint.fieldScores) as number[];
		const totalDetail = scores.reduce(
			(acc: number, val: number) => acc + val,
			0,
		);
		return Math.round(totalDetail / 5);
	}, [blueprint]);

	const canGenerate = useMemo(() => {
		return messages.length >= 2 && infoScore >= 20;
	}, [messages.length, infoScore]);

	const handleSendMessage = async (text: string) => {
		const userMsg: Message = {
			id: Date.now().toString(),
			role: "user",
			content: text,
			timestamp: Date.now(),
		};

		const newMessages = [...messages, userMsg];
		setMessages(newMessages);
		setIsChatLoading(true);
		setIsBlueprintLoading(true);

		try {
			// Add placeholder for assistant response
			addMessage("assistant", "");

			await apiClient.streamChat(
				text,
				newMessages.map((m) => ({ role: m.role, content: m.content })),
				blueprint,
				(event) => {
					if (event.type === "token") {
						// Update the last message (streaming text)
						useChatStore.setState((state) => {
							const msgs = [...state.messages];
							const lastMsg = msgs[msgs.length - 1];
							if (lastMsg && lastMsg.role === "assistant") {
								lastMsg.content += event.data.text;
							}
							return { messages: msgs };
						});
					} else if (event.type === "status") {
						// Optional: Show status (e.g. "Analyzing...")
						// For now, we just log or could add a status indicator in UI
						console.log("Status:", event.data.message);
					} else if (event.type === "blueprint_update") {
						// Update blueprint real-time
						updateBlueprint(event.data);
						setIsBlueprintLoading(false); // Stop loading spinner if we get data
					} else if (event.type === "error") {
						console.error("Stream error:", event.data);
						addMessage("assistant", `\n[System Error: ${event.data.message}]`);
					}
				},
			);
		} catch (error) {
			console.error("Critical initiation error:", error);
			addMessage("assistant", "Connection to QuestForge Server failed.");
		} finally {
			setIsChatLoading(false);
			setIsBlueprintLoading(false);
		}
	};

	const handleGenerate = async () => {
		setAppState(AppState.TRANSITION);

		// Local accumulator for the streaming session
		const currentRoadmap: RoadmapData = {
			id: `rm-${Date.now()}`,
			createdAt: Date.now(),
			title: blueprint.goal || "New Roadmap",
			score: 0,
			summary: "Generating...",
			nodes: [],
			edges: [],
		};

		const updateView = () => {
			// Update store and trigger visualization refresh
			setRoadmap({ ...currentRoadmap }); // Spread to create new reference
			regenerateFlow({ ...currentRoadmap });
		};

		try {
			await apiClient.streamRoadmap(blueprint, (event) => {
				if (event.type === "roadmap_milestones") {
					// 1. Skeleton: Milestones and their sequence
					const milestones = event.data.milestones;
					const newNodes = milestones.map((m: any) => ({
						id: m.id,
						type: "milestone",
						label: m.label,
						is_assumed: m.is_assumed,
						details: m.details ? [m.details] : [],
						data: { ...m }, // Ensure data prop is robust
					}));

					// Create sequential edges between milestones
					const newEdges = [];
					for (let i = 0; i < newNodes.length - 1; i++) {
						newEdges.push({
							id: `e-${newNodes[i].id}-${newNodes[i + 1].id}`,
							source: newNodes[i].id,
							target: newNodes[i + 1].id,
						});
					}

					currentRoadmap.nodes = newNodes;
					currentRoadmap.edges = newEdges;
					updateView();
				} else if (event.type === "roadmap_tasks") {
					// 2. Expansion: Add tasks to a milestone
					const milestoneId = event.data.milestone_id;
					const tasks = event.data.tasks;

					const taskNodes = tasks.map((t: any) => ({
						id: t.id,
						type: "task", // These will act as "Steps" in the visualization (2nd column)
						label: t.label,
						status: t.status,
						details: t.details ? [t.details] : [],
						data: { ...t },
					}));

					const taskEdges = taskNodes.map((t: any) => ({
						id: `e-${milestoneId}-${t.id}`,
						source: milestoneId,
						target: t.id,
					}));

					currentRoadmap.nodes.push(...taskNodes);
					currentRoadmap.edges.push(...taskEdges);
					updateView();
				} else if (event.type === "error") {
					console.error("Roadmap stream error:", event.data);
				}
			});
		} catch (e) {
			console.error(e);
			alert("The Oracle's vision is clouded. Please try again.");
			setAppState(AppState.DISCOVERY);
		}
	};

	const regenerateFlow = (data: any) => {
		// Copy of the layout logic from handleGenerate
		const flowNodes: Node[] = [];
		const adjacency = new Map<string, string[]>();
		data.edges.forEach((e: any) => {
			if (!adjacency.has(e.source)) adjacency.set(e.source, []);
			adjacency.get(e.source)?.push(e.target);
		});

		let currentY = 0;
		const milestones = data.nodes.filter((n: any) => n.type === "milestone");

		milestones.forEach((milestone: any) => {
			flowNodes.push({
				id: milestone.id,
				type: "roadmapNode",
				data: {
					label: milestone.label,
					is_assumed: milestone.is_assumed,
					type: milestone.type,
					details: milestone.details,
				},
				position: { x: 0, y: currentY },
			});

			const stepIds = adjacency.get(milestone.id) || [];
			const steps = stepIds
				.map((id) => data.nodes.find((n: any) => n.id === id))
				.filter((n) => n) as RoadmapNode[];

			let stepYStart = currentY;

			steps.forEach((step, _stepIndex) => {
				const taskIds = adjacency.get(step.id) || [];
				const tasks = taskIds
					.map((id) => data.nodes.find((n: any) => n.id === id))
					.filter((n) => n) as RoadmapNode[];

				const requiredHeight = Math.max(tasks.length * 100, 150);

				flowNodes.push({
					id: step.id,
					type: "roadmapNode",
					data: {
						label: step.label,
						is_assumed: step.is_assumed,
						type: step.type,
						details: step.details,
					},
					position: { x: 400, y: stepYStart + requiredHeight / 2 - 50 },
				});

				tasks.forEach((task, taskIndex) => {
					flowNodes.push({
						id: task.id,
						type: "roadmapNode",
						data: {
							label: task.label,
							is_assumed: task.is_assumed,
							type: task.type,
							details: task.details,
						},
						position: { x: 800, y: stepYStart + taskIndex * 100 },
					});
				});

				stepYStart += requiredHeight + 50;
			});

			currentY = Math.max(currentY + 200, stepYStart + 100);
		});

		const flowEdges: Edge[] = data.edges.map((e: any) => ({
			id: e.id,
			source: e.source,
			target: e.target,
			animated: true,
			style: { stroke: "#3d84f5", strokeWidth: 2 },
		}));

		setFlowNodes(flowNodes);
		setFlowEdges(flowEdges);
		setAppState(AppState.VISUALIZATION);
	};

	const handleLoadRoadmap = (id: string) => {
		const target = roadmapHistory.find((r) => r.id === id);
		if (target) {
			loadRoadmap(id);
			regenerateFlow(target);
		}
		setShowHistory(false);
	};

	return (
		<div className="flex w-full h-full overflow-hidden">
			{/* Left: Chat Panel (Oracle) */}
			<div className="w-1/2 lg:w-2/5 border-r border-slate-800 flex flex-col h-full bg-[#101722] relative z-20 shadow-2xl">
				<header className="p-6 border-b border-slate-800 bg-[#101722]/80 backdrop-blur-md flex items-center justify-between">
					<div className="flex items-center gap-3">
						<div className="p-2 bg-blue-600 rounded-xl shadow-[0_0_15px_rgba(59,130,246,0.5)]">
							<Swords className="w-6 h-6 text-white" />
						</div>
						<div>
							<h1 className="font-black text-xl tracking-tighter uppercase italic">
								QuestForge <span className="text-blue-500">AI</span>
							</h1>
							<p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
								Oracle Session v2.5
							</p>
						</div>
					</div>

					{roadmapHistory.length > 0 && (
						<div className="relative">
							<button
								type="button"
								onClick={() => setShowHistory(!showHistory)}
								className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
								title="Quest History"
							>
								<History className="w-5 h-5" />
							</button>

							{showHistory && (
								<div className="absolute right-0 top-full mt-2 w-64 bg-[#1a2436] border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
									<div className="p-3 border-b border-slate-700 bg-[#101722]/50">
										<h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
											Quest History
										</h3>
									</div>
									<div className="max-h-64 overflow-y-auto">
										{roadmapHistory.map((r) => (
											<button
												key={r.id}
												type="button"
												onClick={() => handleLoadRoadmap(r.id)}
												className="w-full text-left p-3 hover:bg-slate-800 border-b border-slate-800/50 last:border-0 transition-colors group"
											>
												<p className="text-sm font-bold text-slate-200 group-hover:text-blue-400 truncate">
													{r.title}
												</p>
												<p className="text-[10px] text-slate-500 mt-1">
													{new Date(r.createdAt).toLocaleDateString()}
												</p>
											</button>
										))}
									</div>
								</div>
							)}
						</div>
					)}
				</header>
				<div className="flex-1 overflow-hidden">
					<ChatPanel
						onSendMessage={handleSendMessage}
						onSkip={handleGenerate}
						canGenerate={canGenerate}
						score={infoScore}
						isCalculating={isChatLoading}
					/>
				</div>
			</div>

			{/* Right: Quest Progress & Blueprint */}
			<div className="flex-1 bg-[#0c121b] flex flex-col overflow-y-auto relative">
				<div className="absolute inset-0 bg-grid-pattern opacity-10"></div>
				<div className="relative p-8 space-y-8 max-w-xl mx-auto w-full">
					<ScoreGauge
						score={infoScore}
						readinessTips={blueprint.readinessTips}
						successTips={blueprint.successTips}
						isCalculating={isBlueprintLoading}
					/>
					<BlueprintPreview />
				</div>
			</div>
		</div>
	);
}
