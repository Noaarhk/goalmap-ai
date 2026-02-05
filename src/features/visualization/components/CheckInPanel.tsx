import {
	BrainCircuit,
	Check,
	ChevronDown,
	Loader2,
	Minus,
	Plus,
	PlusCircle,
	TrendingUp,
	X,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
	apiClient,
	type CheckInAnalyzeResponse,
	type NodeUpdate,
} from "../../../services/apiClient";
import type { RoadmapNode } from "../../../types";
import { useRoadmapStore } from "../../../stores";

interface EditableUpdate extends NodeUpdate {
	selected: boolean;
}

interface CheckInPanelProps {
	roadmapId: string;
	nodes: RoadmapNode[];
	onUpdatesConfirmed: (updatedNodeIds: string[]) => void;
}

export function CheckInPanel({
	roadmapId,
	nodes,
	onUpdatesConfirmed,
}: CheckInPanelProps) {
	const [checkInInput, setCheckInInput] = useState("");
	const [isAnalyzing, setIsAnalyzing] = useState(false);
	const [pendingResult, setPendingResult] = useState<CheckInAnalyzeResponse | null>(null);
	const [editableUpdates, setEditableUpdates] = useState<EditableUpdate[]>([]);
	const [isConfirming, setIsConfirming] = useState(false);
	const [showAddNode, setShowAddNode] = useState(false);

	// Sync editable updates when pending result changes
	useEffect(() => {
		if (pendingResult) {
			setEditableUpdates(
				pendingResult.proposed_updates.map((u) => ({ ...u, selected: true }))
			);
		} else {
			setEditableUpdates([]);
		}
	}, [pendingResult]);

	const getNodeLabel = (nodeId: string) => {
		return nodes.find((n) => n.id === nodeId)?.label || "Unknown Node";
	};

	// Get nodes not already in updates (for "Add Node" dropdown)
	const availableNodes = nodes.filter(
		(n) => !editableUpdates.some((u) => u.node_id === n.id)
	);

	const handleAnalyze = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!checkInInput.trim() || isAnalyzing) return;

		console.log("[CheckIn] Starting analysis...", { roadmapId, userInput: checkInInput });
		setIsAnalyzing(true);
		try {
			const result = await apiClient.analyzeCheckIn(roadmapId, checkInInput);
			console.log("[CheckIn] Analysis result:", result);
			setPendingResult(result);
			setCheckInInput("");
		} catch (error) {
			console.error("[CheckIn] Analysis failed:", error);
		} finally {
			setIsAnalyzing(false);
		}
	};

	const toggleUpdateSelection = (nodeId: string) => {
		setEditableUpdates((prev) =>
			prev.map((u) =>
				u.node_id === nodeId ? { ...u, selected: !u.selected } : u
			)
		);
	};

	const adjustProgressDelta = (nodeId: string, delta: number) => {
		setEditableUpdates((prev) =>
			prev.map((u) =>
				u.node_id === nodeId
					? { ...u, progress_delta: Math.max(0, Math.min(100, u.progress_delta + delta)) }
					: u
			)
		);
	};

	const addManualNode = (nodeId: string) => {
		const node = nodes.find((n) => n.id === nodeId);
		if (!node) return;

		setEditableUpdates((prev) => [
			...prev,
			{
				node_id: nodeId,
				progress_delta: 10,
				log_entry: "Manual progress update",
				selected: true,
			},
		]);
		setShowAddNode(false);
	};

	const removeUpdate = (nodeId: string) => {
		setEditableUpdates((prev) => prev.filter((u) => u.node_id !== nodeId));
	};

	const handleConfirm = async () => {
		if (!pendingResult) return;

		const selectedUpdates = editableUpdates.filter((u) => u.selected);
		if (selectedUpdates.length === 0) {
			setPendingResult(null);
			return;
		}

		setIsConfirming(true);
		try {
			const result = await apiClient.confirmCheckIn(
				pendingResult.checkin_id,
				selectedUpdates.map(({ node_id, progress_delta, log_entry }) => ({
					node_id,
					progress_delta,
					log_entry,
				}))
			);
			if (result.success) {
				// Update local state by node ID (UUID)
				const { roadmap, nodes: flowNodes } = useRoadmapStore.getState();
				if (roadmap) {
					// Create a map of node_id -> progress_delta
					const updatesMap = new Map<string, number>();
					for (const update of selectedUpdates) {
						updatesMap.set(update.node_id, update.progress_delta);
					}

					// Update roadmap nodes by ID
					const updatedRoadmapNodes = roadmap.nodes.map((n) => {
						const delta = updatesMap.get(n.id);
						if (delta !== undefined) {
							return { ...n, progress: Math.min(100, (n.progress || 0) + delta) };
						}
						return n;
					});

					// Update flow nodes by ID
					const updatedFlowNodes = flowNodes.map((n) => {
						const delta = updatesMap.get(n.id);
						if (delta !== undefined) {
							return {
								...n,
								data: { ...n.data, progress: Math.min(100, (n.data.progress || 0) + delta) },
							};
						}
						return n;
					});

					// Update store
					useRoadmapStore.setState({
						roadmap: { ...roadmap, nodes: updatedRoadmapNodes },
						nodes: updatedFlowNodes,
					});
				}
				onUpdatesConfirmed(result.updated_nodes);
			}
			setPendingResult(null);
		} catch (error) {
			console.error("Confirm failed:", error);
		} finally {
			setIsConfirming(false);
		}
	};

	const handleCancel = async () => {
		if (!pendingResult) return;

		try {
			await apiClient.rejectCheckIn(pendingResult.checkin_id);
		} catch (error) {
			console.error("Reject failed:", error);
		}
		setPendingResult(null);
	};

	const selectedCount = editableUpdates.filter((u) => u.selected).length;

	// Pending updates confirmation view
	if (pendingResult && editableUpdates.length > 0) {
		return (
			<div className="bg-[#1a2436] border-2 border-emerald-500/50 p-6 rounded-3xl shadow-[0_0_50px_rgba(16,185,129,0.2)] animate-in slide-in-from-bottom-4 duration-300">
				<div className="flex items-center gap-3 mb-4">
					<div className="p-2 bg-emerald-500/20 rounded-lg">
						<BrainCircuit className="w-5 h-5 text-emerald-500" />
					</div>
					<div className="flex-1">
						<h4 className="text-[10px] font-black uppercase tracking-widest text-emerald-400">
							Progress Update Detected
						</h4>
						<p className="text-xs text-slate-400 font-bold">
							{selectedCount} of {editableUpdates.length} updates selected
						</p>
					</div>
				</div>

				<div className="max-h-[250px] overflow-y-auto space-y-3 mb-4 pr-2 custom-scrollbar">
					{editableUpdates.map((update) => (
						<div
							key={update.node_id}
							className={`p-3 rounded-xl border transition-all ${
								update.selected
									? "bg-slate-900/50 border-slate-700"
									: "bg-slate-900/20 border-slate-800/50 opacity-50"
							}`}
						>
							<div className="flex items-center gap-3">
								{/* Checkbox */}
								<button
									type="button"
									onClick={() => toggleUpdateSelection(update.node_id)}
									className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
										update.selected
											? "bg-emerald-500 border-emerald-500"
											: "border-slate-600 hover:border-slate-500"
									}`}
								>
									{update.selected && <Check className="w-3 h-3 text-white" />}
								</button>

								{/* Node label */}
								<span className="flex-1 text-[10px] font-black text-white uppercase tracking-wider">
									{getNodeLabel(update.node_id)}
								</span>

								{/* Progress delta adjuster */}
								<div className="flex items-center gap-1">
									<button
										type="button"
										onClick={() => adjustProgressDelta(update.node_id, -5)}
										disabled={!update.selected}
										className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
									>
										<Minus className="w-3 h-3 text-slate-400" />
									</button>
									<div className="flex items-center gap-1 px-2 py-0.5 bg-emerald-500/10 rounded-full border border-emerald-500/20 min-w-[60px] justify-center">
										<TrendingUp className="w-3 h-3 text-emerald-500" />
										<span className="text-[10px] font-black text-emerald-400">
											+{update.progress_delta}%
										</span>
									</div>
									<button
										type="button"
										onClick={() => adjustProgressDelta(update.node_id, 5)}
										disabled={!update.selected}
										className="p-1 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed"
									>
										<Plus className="w-3 h-3 text-slate-400" />
									</button>
								</div>

								{/* Remove button (for manually added) */}
								{!pendingResult.proposed_updates.some((p) => p.node_id === update.node_id) && (
									<button
										type="button"
										onClick={() => removeUpdate(update.node_id)}
										className="p-1 rounded hover:bg-red-500/20 text-slate-500 hover:text-red-400"
									>
										<X className="w-3 h-3" />
									</button>
								)}
							</div>

							{/* Log entry */}
							<p className="text-[11px] text-slate-400 italic mt-2 ml-8">
								"{update.log_entry}"
							</p>
						</div>
					))}
				</div>

				{/* Add Node Button */}
				<div className="mb-4 relative">
					{showAddNode ? (
						<div className="bg-slate-900 border border-slate-700 rounded-xl p-2 max-h-[150px] overflow-y-auto">
							<div className="flex items-center justify-between mb-2 px-2">
								<span className="text-[9px] font-bold text-slate-500 uppercase">
									Select a node to add
								</span>
								<button
									type="button"
									onClick={() => setShowAddNode(false)}
									className="text-slate-500 hover:text-white"
								>
									<X className="w-3 h-3" />
								</button>
							</div>
							{availableNodes.length > 0 ? (
								availableNodes.map((node) => (
									<button
										key={node.id}
										type="button"
										onClick={() => addManualNode(node.id)}
										className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
									>
										{node.label}
									</button>
								))
							) : (
								<p className="text-xs text-slate-500 px-3 py-2">
									All nodes already added
								</p>
							)}
						</div>
					) : (
						<button
							type="button"
							onClick={() => setShowAddNode(true)}
							className="w-full py-2 border border-dashed border-slate-700 rounded-xl text-slate-500 hover:text-slate-300 hover:border-slate-600 transition-all flex items-center justify-center gap-2 text-[10px] font-bold uppercase"
						>
							<PlusCircle className="w-3 h-3" /> Add Another Node
						</button>
					)}
				</div>

				<div className="flex gap-3">
					<button
						type="button"
						onClick={handleConfirm}
						disabled={isConfirming || selectedCount === 0}
						className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-[10px] font-black uppercase tracking-[0.2em] shadow-lg transition-all flex items-center justify-center gap-2"
					>
						{isConfirming ? (
							<Loader2 className="w-4 h-4 animate-spin" />
						) : (
							<>
								<Check className="w-4 h-4" /> Confirm {selectedCount} Updates
							</>
						)}
					</button>
					<button
						type="button"
						onClick={handleCancel}
						disabled={isConfirming}
						className="px-6 py-3 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-400 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
					>
						<X className="w-4 h-4" />
					</button>
				</div>
			</div>
		);
	}

	// Empty results view
	if (pendingResult && pendingResult.proposed_updates.length === 0) {
		return (
			<div className="bg-[#1a2436] border border-amber-500/30 p-6 rounded-3xl">
				<div className="flex items-center gap-3 mb-4">
					<div className="p-2 bg-amber-500/20 rounded-lg">
						<BrainCircuit className="w-5 h-5 text-amber-500" />
					</div>
					<div>
						<h4 className="text-[10px] font-black uppercase tracking-widest text-amber-400">
							No Matches Found
						</h4>
						<p className="text-xs text-slate-400">
							Couldn't match your update to any nodes. Try being more specific.
						</p>
					</div>
				</div>
				<button
					type="button"
					onClick={() => setPendingResult(null)}
					className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
				>
					Try Again
				</button>
			</div>
		);
	}

	// Default input form
	return (
		<form
			onSubmit={handleAnalyze}
			className="bg-[#1a2436]/95 backdrop-blur-md border border-slate-700 p-4 rounded-3xl shadow-2xl flex flex-col gap-3 relative overflow-hidden group"
		>
			<div className="absolute top-0 left-0 h-1 bg-gradient-to-r from-blue-600 via-emerald-500 to-blue-600 w-full opacity-50 group-hover:opacity-100 transition-opacity" />
			<div className="flex items-center justify-between">
				<div className="flex items-center gap-2">
					<BrainCircuit className="w-4 h-4 text-emerald-500" />
					<span className="text-[10px] font-black uppercase tracking-widest text-emerald-400">
						Daily Progress Sync
					</span>
				</div>
				<span className="text-[9px] font-bold text-slate-500">
					Describe what you accomplished...
				</span>
			</div>
			<div className="flex gap-2">
				<input
					type="text"
					value={checkInInput}
					onChange={(e) => setCheckInInput(e.target.value)}
					placeholder="Ex: I finished the UI design phase and started the API integration."
					className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-3 text-xs focus:ring-2 focus:ring-emerald-500/50 outline-none placeholder-slate-600 transition-all text-white"
					disabled={isAnalyzing}
				/>
				<button
					type="submit"
					disabled={isAnalyzing || !checkInInput.trim()}
					className="px-6 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:bg-slate-700 rounded-xl transition-all flex items-center justify-center min-w-[120px]"
				>
					{isAnalyzing ? (
						<Loader2 className="w-4 h-4 animate-spin text-white" />
					) : (
						<span className="text-[10px] font-black uppercase tracking-widest text-white">
							Analyze
						</span>
					)}
				</button>
			</div>
		</form>
	);
}
