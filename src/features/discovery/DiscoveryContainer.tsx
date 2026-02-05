import { Check, Edit2, History, LogOut, Plus, Swords, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { Edge, Node } from "reactflow";
import ScoreGauge from "../../components/common/ScoreGauge";
import { apiClient } from "../../services/apiClient";
import {
	useAppStore,
	useAuthStore,
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
	const {
		messages,
		addMessage,
		setMessages,
		conversations,
		setConversations,

		loadConversation,
		updateConversation,
		currentConversationId,
	} = useChatStore();
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
		setStreamingGoal,
		setStreamingStatus,
		setStreamingStep,
		setStreamingMilestones,
		addStreamingActions,
		resetStreaming,
	} = useRoadmapStore();

	const [showHistory, setShowHistory] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editTitle, setEditTitle] = useState("");

	// Get auth state
	const { isInitialized, user } = useAuthStore();

	// --- Data Loading ---
	useEffect(() => {
		// Wait for auth to be initialized and user to be logged in
		if (!isInitialized || !user) {
			console.log("[DiscoveryContainer] Waiting for auth...", {
				isInitialized,
				user: !!user,
			});
			return;
		}

		const loadData = async () => {
			console.log("[DiscoveryContainer] Loading data...");
			try {
				// 1. Load Roadmaps
				const roadmaps = await apiClient.getRoadmaps();
				console.log("[DiscoveryContainer] Loaded roadmaps:", roadmaps);
				const historyData = roadmaps.map((r: any) => {
					// Transform API nodes to frontend format
					const transformedNodes = (r.nodes || []).map((n: any) => ({
						id: n.id,
						label: n.label,
						type: n.type,
						is_assumed: n.is_assumed,
						details: n.details ? [n.details] : [],
						status: n.status,
						order: n.order,
						progress: 0,
						startDate: n.start_date,
						endDate: n.end_date,
						parentId: n.parent_id,
					}));

					// Generate edges from parent_id relationships
					const edges = transformedNodes
						.filter((n: any) => n.parentId)
						.map((n: any) => ({
							id: `e-${n.parentId}-${n.id}`,
							source: n.parentId,
							target: n.id,
						}));

					return {
						id: r.id,
						title: r.title,
						createdAt: new Date(r.created_at).getTime(),
						score: 0,
						summary: r.goal || "",
						nodes: transformedNodes,
						edges,
					};
				});
				console.log("[DiscoveryContainer] Transformed history:", historyData);
				useRoadmapStore.getState().setHistory(historyData);

				// 2. Load Conversations
				const conversations = await apiClient.getConversations();
				useChatStore.getState().setConversations(
					conversations.map((c: any) => ({
						id: c.id,
						title: c.title || "Untitled Quest",
						messages: c.messages || [],
						createdAt: new Date(c.created_at).getTime(),
						updatedAt: new Date(c.updated_at).getTime(),
					})),
				);

				if (conversations.length > 0) {
					// Load the most recent one
					const latest = conversations[0];
					useChatStore
						.getState()
						.loadConversation(latest.id, latest.messages || []);

					// Map API response (snake_case) to Frontend BlueprintData (camelCase)
					const rawBp = latest.blueprint || {};
					const mappedBp = {
						...rawBp,
						fieldScores: rawBp.field_scores || rawBp.fieldScores,
						readinessTips: rawBp.readiness_tips || rawBp.readinessTips,
						successTips: rawBp.success_tips || rawBp.successTips,
						goal: rawBp.end_point || rawBp.goal, // DB stores as end_point
						why: Array.isArray(rawBp.motivations)
							? rawBp.motivations.join("\n")
							: rawBp.why, // DB stores as list
					};
					useBlueprintStore.getState().setBlueprint(mappedBp);
				} else {
					// Create a new one
					const newConv = await apiClient.createConversation("New Quest");
					useChatStore.getState().setConversations([
						{
							id: newConv.id,
							title: newConv.title,
							messages: [],
							createdAt: Date.now(),
							updatedAt: Date.now(),
						},
					]);
					useChatStore.getState().loadConversation(newConv.id, []);
				}
			} catch (e) {
				console.error("Failed to load initial data", e);
			}
		};
		loadData();
	}, [isInitialized, user]);

	const infoScore = useMemo(() => {
		if (!blueprint.fieldScores) {
			const fields = ["goal", "why", "timeline", "obstacles", "resources"];
			const filledCount = fields.filter((f) => {
				const val = (blueprint as Record<string, any>)[f];
				return Array.isArray(val) ? val.length > 0 : !!val;
			}).length;
			return Math.min(filledCount * 4, 20); // 5 fields * 4 = 20 max
		}
		const { milestones, ...restScores } = blueprint.fieldScores || {};
		const activeScores = Object.values(restScores) as number[];
		const totalDetail = activeScores.reduce(
			(acc: number, val: number) => acc + val,
			0,
		);
		return Math.round(totalDetail / 5);
	}, [blueprint]);

	const canGenerate = useMemo(() => {
		return messages.length >= 2 && infoScore >= 20;
	}, [messages.length, infoScore]);

	const handleSendMessage = async (text: string) => {
		const { currentConversationId } = useChatStore.getState();

		if (!currentConversationId) {
			console.error("No active conversation. Cannot send message.");
			return;
		}

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
				currentConversationId,
				(event) => {
					if (event.type === "token") {
						// Update the last message (streaming text)
						setIsChatLoading(true); // Switch back to simple loading state
						useChatStore.setState((state) => {
							const msgs = [...state.messages];
							const lastMsg = msgs[msgs.length - 1];
							if (lastMsg && lastMsg.role === "assistant") {
								lastMsg.content += event.data.text;
							}
							return { messages: msgs };
						});
					} else if (event.type === "status") {
						// Show specific status (e.g. "Analyzing Goal...")
						const statusMap: Record<string, string> = {
							analyze_input: "Analyzing your quest...",
							extract_goal: "Forging the heart of your mission...",
							extract_tactics: "Mapping out the strategy...",
							generate_response: "The Oracle is speaking...",
							analyze_turn: "Consulting the archives...",
							generate_chat: "Crafting response...",
						};
						setIsChatLoading(statusMap[event.data.node] || event.data.message);
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
		const { currentConversationId } = useChatStore.getState();

		if (!currentConversationId) {
			console.error("Cannot generate roadmap without an active conversation");
			return;
		}

		setAppState(AppState.TRANSITION);
		resetStreaming(); // Reset streaming state for fresh TransitionView

		// Optimize: Set goal immediately for TransitionView
		setStreamingGoal(blueprint.goal || "New Roadmap");
		setStreamingStatus("Analyzing your goal...");
		setStreamingStep(1); // Step 1: Goal Analysis

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

			// Persist the roadmap via API (already done in stream, but we might want to refresh list)
			setTimeout(() => {
				apiClient.getRoadmaps().then((roadmaps) => {
					useRoadmapStore.getState().setHistory(roadmaps);
				});
			}, 1000);
		};

		try {
			await apiClient.streamRoadmap(
				blueprint,
				currentConversationId,
				(event) => {
					if (event.type === "roadmap_skeleton") {
						// 1. Skeleton: Goal with milestones (no edges from server)
						const { goal } = event.data;

						// Update streaming state for TransitionView
						setStreamingGoal(goal.label);
						setStreamingStatus("Designing milestones...");
						setStreamingStep(2); // Step 2: Milestone Design
						setStreamingMilestones(
							goal.milestones.map((m: any) => ({
								id: m.id,
								label: m.label,
								status: "pending" as const,
							})),
						);

						// Create goal node
						const goalNode = {
							id: goal.id,
							type: "goal" as const,
							label: goal.label,
							is_assumed: false,
							details: goal.details ? [goal.details] : [],
						};

						// Create milestone nodes
						const milestoneNodes = goal.milestones.map((m: any) => ({
							id: m.id,
							type: "milestone" as const,
							label: m.label,
							is_assumed: m.is_assumed,
							details: m.details ? [m.details] : [],
						}));

						// Generate edges dynamically (goal -> milestones)
						const milestoneEdges = goal.milestones.map((m: any) => ({
							id: `e-${goal.id}-${m.id}`,
							source: goal.id,
							target: m.id,
						}));

						currentRoadmap.nodes = [goalNode, ...milestoneNodes];
						currentRoadmap.edges = milestoneEdges;
						currentRoadmap.summary = goal.details || "Quest roadmap";
						// Don't call updateView() here - stay in TransitionView to show streaming progress
					} else if (event.type === "roadmap_actions") {
						// 2. Expansion: Add actions to a milestone
						const milestoneId = event.data.milestone_id;
						const actions = event.data.actions;

						// Update streaming state for TransitionView
						if (useRoadmapStore.getState().streamingStep < 3) {
							setStreamingStep(3); // Step 3: Action Planning (only set once)
						}
						setStreamingStatus(`Planning actions for milestone...`);
						addStreamingActions(
							actions.map((a: any) => ({
								milestoneId,
								id: a.id,
								label: a.label,
							})),
						);

						// Update milestone status to done
						const { streamingMilestones } = useRoadmapStore.getState();
						setStreamingMilestones(
							streamingMilestones.map((m) =>
								m.id === milestoneId ? { ...m, status: "done" as const } : m,
							),
						);

						const actionNodes = actions.map((a: any) => ({
							id: a.id,
							type: "action" as const,
							label: a.label,
							is_assumed: false,
							details: a.details ? [a.details] : [],
						}));

						const actionEdges = actionNodes.map((a: any) => ({
							id: `e-${milestoneId}-${a.id}`,
							source: milestoneId,
							target: a.id,
						}));

						currentRoadmap.nodes.push(...actionNodes);
						currentRoadmap.edges.push(...actionEdges);
						// Don't call updateView() here - stay in TransitionView to show streaming progress
					} else if (event.type === "roadmap_direct_actions") {
						setStreamingStatus("Finalizing roadmap...");
						setStreamingStep(4); // Step 4: Finalizing
						// 3. Direct Actions: Add actions directly to goal
						const actions = event.data.actions;
						const goalNode = currentRoadmap.nodes.find(
							(n) => n.type === "goal",
						);
						if (goalNode && actions.length > 0) {
							const actionNodes = actions.map((a: any) => ({
								id: a.id,
								type: "action" as const,
								label: a.label,
								is_assumed: false,
								details: a.details ? [a.details] : [],
								startDate: a.start_date || a.startDate,
								endDate: a.end_date || a.endDate,
								parentId: a.parent_id || a.parentId,
							}));

							const actionEdges = actionNodes.map((a: any) => ({
								id: `e-${goalNode.id}-${a.id}`,
								source: goalNode.id,
								target: a.id,
							}));

							currentRoadmap.nodes.push(...actionNodes);
							currentRoadmap.edges.push(...actionEdges);
							updateView();
						}
					} else if (event.type === "error") {
						console.error("Roadmap stream error:", event.data);
					}
				},
			);

			// Fallback: If stream completed but direct_actions didn't fire (edge case)
			if (currentRoadmap.nodes.length > 0) {
				updateView();
			}
		} catch (e) {
			console.error(e);
			alert("The Oracle's vision is clouded. Please try again.");
			setAppState(AppState.DISCOVERY);
		}
	};

	const regenerateFlow = (data: any) => {
		// 3-tier layout: Goal at top -> Milestones in middle -> Actions at bottom
		const flowNodes: Node[] = [];
		const adjacency = new Map<string, string[]>();
		data.edges.forEach((e: any) => {
			if (!adjacency.has(e.source)) adjacency.set(e.source, []);
			adjacency.get(e.source)?.push(e.target);
		});

		// Find goal node (top level)
		const goalNode = data.nodes.find((n: any) => n.type === "goal");
		const milestones = data.nodes.filter((n: any) => n.type === "milestone");

		// Layout constants
		const GOAL_Y = 0;
		const MILESTONE_Y = 300;
		const ACTION_Y = 600;
		const NODE_SPACING_X = 350;

		// Place goal node at top center
		if (goalNode) {
			const totalWidth = (milestones.length - 1) * NODE_SPACING_X;
			flowNodes.push({
				id: goalNode.id,
				type: "roadmapNode",
				data: {
					label: goalNode.label,
					is_assumed: goalNode.is_assumed,
					type: goalNode.type,
					details: goalNode.details,
				},
				position: { x: totalWidth / 2, y: GOAL_Y },
			});
		}

		// Place milestones in a row below goal
		milestones.forEach((milestone: any, mIdx: number) => {
			const xPos = mIdx * NODE_SPACING_X;
			flowNodes.push({
				id: milestone.id,
				type: "roadmapNode",
				data: {
					label: milestone.label,
					is_assumed: milestone.is_assumed,
					type: milestone.type,
					details: milestone.details,
				},
				position: { x: xPos, y: MILESTONE_Y },
			});

			// Get actions for this milestone
			const actionIds = adjacency.get(milestone.id) || [];
			const actions = actionIds
				.map((id) => data.nodes.find((n: any) => n.id === id))
				.filter(
					(n) => n && (n.type === "action" || n.type === "task"),
				) as RoadmapNode[];

			// Place actions below their milestone
			actions.forEach((action, aIdx) => {
				const actionXOffset = (aIdx - (actions.length - 1) / 2) * 150;
				flowNodes.push({
					id: action.id,
					type: "roadmapNode",
					data: {
						label: action.label,
						is_assumed: action.is_assumed,
						type: action.type,
						details: action.details,
					},
					position: { x: xPos + actionXOffset, y: ACTION_Y + aIdx * 80 },
				});
			});
		});

		// Place goal direct actions (cross-cutting actions) to the right of milestones
		if (goalNode) {
			const goalActionIds = adjacency.get(goalNode.id) || [];
			const goalActions = goalActionIds
				.map((id) => data.nodes.find((n: any) => n.id === id))
				.filter(
					(n) => n && (n.type === "action" || n.type === "task"),
				) as RoadmapNode[];

			const rightMostX = milestones.length * NODE_SPACING_X;
			goalActions.forEach((action, aIdx) => {
				flowNodes.push({
					id: action.id,
					type: "roadmapNode",
					data: {
						label: action.label,
						is_assumed: action.is_assumed,
						type: action.type,
						details: action.details,
					},
					position: { x: rightMostX + 100, y: MILESTONE_Y + aIdx * 100 },
				});
			});
		}

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

	const _handleLoadRoadmap = (id: string) => {
		const target = roadmapHistory.find((r) => r.id === id);
		if (target) {
			loadRoadmap(id);
			regenerateFlow(target);
		}
		setShowHistory(false);
	};

	const handleNewChat = async () => {
		try {
			setIsBlueprintLoading(true);
			// 1. Create new conversation on backend
			const newConv = await apiClient.createConversation("New Quest");

			// 2. Update store
			const newConversationObj = {
				id: newConv.id,
				title: newConv.title,
				messages: [],
				createdAt: Date.now(),
				updatedAt: Date.now(),
			};

			setConversations([newConversationObj, ...conversations]);
			loadConversation(newConv.id, []);

			// 3. Reset Blueprint
			useBlueprintStore.getState().reset();

			// 4. Reset Roadmap/Flow? (Maybe keep history but clear current view)
			setRoadmap({
				id: "",
				title: "",
				score: 0,
				summary: "",
				createdAt: Date.now(),
				nodes: [],
				edges: [],
			});
			setFlowNodes([]);
			setFlowEdges([]);
			setAppState(AppState.DISCOVERY);
		} catch (e) {
			console.error("Failed to create new chat", e);
		} finally {
			setIsBlueprintLoading(false);
		}
	};

	const handleLoadConversation = async (id: string) => {
		try {
			setIsChatLoading(true);
			const conv = await apiClient.getConversation(id);

			// Update Chat Store
			loadConversation(conv.id, conv.messages || []);

			// Update Blueprint Store
			const rawBp = conv.blueprint || {};
			const mappedBp = {
				...rawBp,
				fieldScores: rawBp.field_scores || rawBp.fieldScores,
				readinessTips: rawBp.readiness_tips || rawBp.readinessTips,
				successTips: rawBp.success_tips || rawBp.successTips,
				goal: rawBp.end_point || rawBp.goal,
				why: Array.isArray(rawBp.motivations)
					? rawBp.motivations.join("\n")
					: rawBp.why,
			};
			useBlueprintStore.getState().setBlueprint(mappedBp);

			// Clear Roadmap View (since we switched context)
			setFlowNodes([]);
			setFlowEdges([]);
			setAppState(AppState.DISCOVERY);

			setShowHistory(false);
		} catch (e) {
			console.error("Failed to load conversation", e);
		} finally {
			setIsChatLoading(false);
		}
	};

	const startEditing = (
		e: React.MouseEvent,
		id: string,
		currentTitle: string,
	) => {
		e.stopPropagation();
		setEditingId(id);
		setEditTitle(currentTitle);
	};

	const cancelEditing = (e: React.MouseEvent) => {
		e.stopPropagation();
		setEditingId(null);
		setEditTitle("");
	};

	const saveTitle = async (e: React.MouseEvent, id: string) => {
		e.stopPropagation();
		if (!editTitle.trim()) return;

		try {
			// Optimistic update
			updateConversation(id, { title: editTitle });
			setEditingId(null);

			// API call
			await apiClient.updateConversation(id, { title: editTitle });
		} catch (error) {
			console.error("Failed to update title", error);
			// Revert on failure? For now just log
		}
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

					<div className="flex items-center gap-2">
						<button
							type="button"
							onClick={handleNewChat}
							className="p-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white transition-colors flex items-center gap-2"
							title="New Quest"
						>
							<Plus className="w-4 h-4" />
							<span className="text-xs font-bold uppercase tracking-wider hidden sm:inline">
								New Quest
							</span>
						</button>

						{conversations.length > 0 && (
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
									<div className="absolute right-0 top-full mt-2 w-72 bg-[#1a2436] border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden">
										{/* Roadmaps Section */}
										{roadmapHistory.length > 0 && (
											<>
												<div className="p-3 border-b border-slate-700 bg-emerald-900/20">
													<h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
														Saved Roadmaps
													</h3>
												</div>
												<div className="max-h-40 overflow-y-auto border-b border-slate-700">
													{roadmapHistory.map((r) => (
														<button
															key={r.id}
															type="button"
															onClick={() => {
																loadRoadmap(r.id);
																regenerateFlow(r);
																setShowHistory(false);
															}}
															className="w-full text-left p-3 hover:bg-emerald-900/20 border-b border-slate-800/50 last:border-0 transition-colors flex items-center gap-3"
														>
															<div className="w-2 h-2 rounded-full bg-emerald-500" />
															<div className="flex-1 overflow-hidden">
																<p className="text-sm font-bold text-slate-200 truncate">
																	{r.title || "Untitled Roadmap"}
																</p>
																<p className="text-[10px] text-slate-500">
																	{new Date(r.createdAt).toLocaleDateString()}
																</p>
															</div>
														</button>
													))}
												</div>
											</>
										)}

										{/* Conversations Section */}
										<div className="p-3 border-b border-slate-700 bg-[#101722]/50">
											<h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
												Quest History
											</h3>
										</div>
										<div className="max-h-64 overflow-y-auto">
											{conversations.map((c) => (
												<button
													key={c.id}
													type="button"
													onClick={() => handleLoadConversation(c.id)}
													className={`w-full text-left p-3 hover:bg-slate-800 border-b border-slate-800/50 last:border-0 transition-colors group ${currentConversationId === c.id ? "bg-slate-800/50" : ""} flex items-center justify-between group`}
												>
													<div className="overflow-hidden flex-1 mr-2">
														{editingId === c.id ? (
															<div
																className="flex items-center gap-1"
																onClick={(e) => e.stopPropagation()}
															>
																<input
																	type="text"
																	value={editTitle}
																	onChange={(e) => setEditTitle(e.target.value)}
																	className="bg-slate-900 border border-blue-500 rounded px-1 py-0.5 text-xs text-white w-full focus:outline-none"
																	onKeyDown={(e) => {
																		if (e.key === "Enter")
																			saveTitle(e as any, c.id);
																		if (e.key === "Escape")
																			cancelEditing(e as any);
																	}}
																/>
																<button
																	type="button"
																	onClick={(e) => saveTitle(e, c.id)}
																	className="p-1 hover:bg-blue-900/50 rounded text-blue-400"
																>
																	<Check className="w-3 h-3" />
																</button>
																<button
																	type="button"
																	onClick={cancelEditing}
																	className="p-1 hover:bg-red-900/50 rounded text-red-400"
																>
																	<X className="w-3 h-3" />
																</button>
															</div>
														) : (
															<>
																<p
																	className={`text-sm font-bold truncate ${currentConversationId === c.id ? "text-blue-400" : "text-slate-200 group-hover/text:text-blue-400"}`}
																>
																	{c.title || "Untitled Quest"}
																</p>
																<p className="text-[10px] text-slate-500 mt-1">
																	{new Date(c.createdAt).toLocaleDateString()}
																</p>
															</>
														)}
													</div>

													{editingId !== c.id && (
														<button
															type="button"
															onClick={(e) =>
																startEditing(e, c.id, c.title || "")
															}
															className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-all"
															title="Rename"
														>
															<Edit2 className="w-3 h-3" />
														</button>
													)}
												</button>
											))}
										</div>
									</div>
								)}
							</div>
						)}
					</div>
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

				<div className="absolute top-6 right-6 z-30">
					<button
						type="button"
						onClick={() => useAuthStore.getState().signOut()}
						className="p-2 bg-slate-900/50 hover:bg-red-900/20 border border-slate-800 hover:border-red-900/50 rounded-lg text-slate-400 hover:text-red-400 transition-all backdrop-blur-sm"
						title="Log Out"
					>
						<LogOut className="w-5 h-5" />
					</button>
				</div>

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
