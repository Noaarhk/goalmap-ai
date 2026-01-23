import { History, Swords } from "lucide-react";
import { useMemo, useState } from "react";
import type { Edge, Node } from "reactflow";
import ScoreGauge from "../../components/common/ScoreGauge";
import {
	extractBlueprintTactics,
	generateBlueprintTips,
	generateRoadmap,
	getAssistantResponse,
} from "../../services/gemini";
import {
	useAppStore,
	useBlueprintStore,
	useChatStore,
	useRoadmapStore,
} from "../../stores";
import { AppState, type Message, type RoadmapNode } from "../../types";
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
		// Optimistic update
		const newMessages = [...messages, userMsg];
		setMessages(newMessages);
		setIsChatLoading(true);
		setIsBlueprintLoading(true);

		try {
			// 1. Unified Oracle Response (Message + Identity Update)
			const extractionPayload = newMessages.map((m) => ({
				role: m.role,
				content: m.content,
			}));

			getAssistantResponse(extractionPayload)
				.then((res) => {
					// Atomically update Chat AND Blueprint (Identity)
					addMessage("assistant", res.message);
					if (res.statusSummary && Object.keys(res.statusSummary).length > 0) {
						updateBlueprint(res.statusSummary);
					}
				})
				.catch((err) => {
					console.error("Oracle Response failed:", err);
					addMessage(
						"assistant",
						"The Oracle's connection is weak. I am having trouble responding right now.",
					);
				})
				.finally(() => setIsChatLoading(false));

			// 2. Tactical & Strategic Background Analysis
			extractBlueprintTactics(extractionPayload)
				.then(async (tacticsRes) => {
					if (tacticsRes && Object.keys(tacticsRes).length > 0) {
						updateBlueprint(tacticsRes);

						// 3. Tip Generation (Deepest stage)
						try {
							const currentBlueprint = useBlueprintStore.getState().blueprint;
							const tips = await generateBlueprintTips(
								{ ...currentBlueprint, ...tacticsRes },
								extractionPayload,
							);
							updateBlueprint(tips);
						} catch (tipErr) {
							console.error("Tips failed:", tipErr);
						}
					}
				})
				.catch((err) => console.error("Tactics failed:", err))
				.finally(() => {
					console.log("Setting isBlueprintLoading to false");
					setIsBlueprintLoading(false);
				});
		} catch (error) {
			console.error("Critical initiation error:", error);
			setIsChatLoading(false);
			setIsBlueprintLoading(false);
		}
	};

	const handleGenerate = async () => {
		setAppState(AppState.TRANSITION);
		try {
			const history = messages.map((m) => `${m.role}: ${m.content}`).join("\n");
			const roadmapData = await generateRoadmap(blueprint, history);
			setRoadmap(roadmapData);

			const flowNodes: Node[] = [];
			const adjacency = new Map<string, string[]>();
			roadmapData.edges.forEach((e) => {
				if (!adjacency.has(e.source)) adjacency.set(e.source, []);
				adjacency.get(e.source)?.push(e.target);
			});

			let currentY = 0;
			const milestones = roadmapData.nodes.filter(
				(n) => n.type === "milestone",
			);

			milestones.forEach((milestone) => {
				// Place Milestone
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

				// Process connected Steps
				const stepIds = adjacency.get(milestone.id) || [];
				const steps = stepIds
					.map((id) => roadmapData.nodes.find((n) => n.id === id))
					.filter((n) => n) as RoadmapNode[];

				let stepYStart = currentY;

				steps.forEach((step, _stepIndex) => {
					// Process connected Tasks (Action Items)
					const taskIds = adjacency.get(step.id) || [];
					const tasks = taskIds
						.map((id) => roadmapData.nodes.find((n) => n.id === id))
						.filter((n) => n) as RoadmapNode[];

					// Calculate height required for this step
					const requiredHeight = Math.max(tasks.length * 100, 150);

					// Place Step
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

					// Place Tasks
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

			// Add edges
			const flowEdges: Edge[] = roadmapData.edges.map((e) => ({
				id: e.id,
				source: e.source,
				target: e.target,
				animated: true,
				style: { stroke: "#3d84f5", strokeWidth: 2 },
			}));

			setFlowNodes(flowNodes);
			setFlowEdges(flowEdges);
			setAppState(AppState.VISUALIZATION);
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
