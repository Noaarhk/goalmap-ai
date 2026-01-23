import { Compass, Package, Scroll, ShieldAlert, Sword } from "lucide-react";
import type React from "react";
import { useBlueprintStore } from "../../../stores";

const BlueprintPreview: React.FC = () => {
	const { blueprint: data } = useBlueprintStore();

	const items = [
		{
			key: "goal",
			label: "Main Objective",
			icon: <Sword className="w-4 h-4" />,
			value: data.goal,
			score: data.fieldScores?.goal || 0,
			color: "text-blue-500",
		},
		{
			key: "why",
			label: "Motivation (Lore)",
			icon: <Compass className="w-4 h-4" />,
			value: data.why,
			score: data.fieldScores?.why || 0,
			color: "text-purple-500",
		},
		{
			key: "timeline",
			label: "Chronicle (Time)",
			icon: <Scroll className="w-4 h-4" />,
			value: data.timeline,
			score: data.fieldScores?.timeline || 0,
			color: "text-amber-500",
		},
		{
			key: "obstacles",
			label: "Bosses & Hazards",
			icon: <ShieldAlert className="w-4 h-4" />,
			value: data.obstacles,
			score: data.fieldScores?.obstacles || 0,
			color: "text-red-500",
		},
		{
			key: "resources",
			label: "Loot & Inventory",
			icon: <Package className="w-4 h-4" />,
			value: data.resources,
			score: data.fieldScores?.resources || 0,
			color: "text-emerald-500",
		},
	];

	return (
		<div className="space-y-4">
			<div className="flex items-center gap-2 px-1 mb-2">
				<Scroll className="w-5 h-5 text-slate-500" />
				<h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-500">
					Quest Journal
				</h3>
			</div>

			<div className="grid gap-3">
				{items.map((item) => (
					<div
						key={item.key}
						className={`group relative p-4 rounded-xl border transition-all duration-300 ${
							item.value
								? "bg-[#1a2436] border-slate-700 shadow-lg"
								: "bg-[#1a2436]/40 border-slate-800/50 opacity-60"
						}`}
					>
						<div className="flex items-center justify-between mb-2">
							<div className="flex items-center gap-2">
								<span className={item.value ? item.color : "text-slate-600"}>
									{item.icon}
								</span>
								<span className="text-[10px] font-black uppercase tracking-widest text-slate-400">
									{item.label}
								</span>
							</div>
							{item.value && (
								<div className="flex items-center gap-1.5">
									<span className="text-[10px] font-bold text-slate-500">
										{item.score}%
									</span>
								</div>
							)}
						</div>

						<p
							className={`text-xs leading-relaxed ${item.value ? "text-slate-200" : "text-slate-600 italic"}`}
						>
							{item.value || "Waiting for scout reports..."}
						</p>

						{item.value && (
							<div className="mt-3 h-1 w-full bg-[#101722] rounded-full overflow-hidden">
								<div
									className={`h-full transition-all duration-1000 ${
										item.score > 70
											? "bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.5)]"
											: item.score > 30
												? "bg-blue-600"
												: "bg-slate-700"
									}`}
									style={{ width: `${item.score}%` }}
								/>
							</div>
						)}
					</div>
				))}
			</div>
		</div>
	);
};

export default BlueprintPreview;
