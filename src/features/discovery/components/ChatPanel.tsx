import { Loader2, Send, Sparkles, Wand2 } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useChatStore } from "../../../stores";

interface ChatPanelProps {
	onSendMessage: (text: string) => void;
	onSkip: () => void;
	canGenerate: boolean;
	score: number;
	isCalculating?: boolean | string;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
	onSendMessage,
	onSkip,
	canGenerate,
	score,
	isCalculating = false,
}) => {
	const { messages } = useChatStore();
	const [input, setInput] = useState("");
	const messagesEndRef = useRef<HTMLDivElement>(null);

	const scrollToBottom = useCallback(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, []);

	useEffect(() => {
		scrollToBottom();
	}, [scrollToBottom]);

	const handleSubmit = (e: React.FormEvent) => {
		e.preventDefault();
		if (!input.trim() || isCalculating) return;
		onSendMessage(input);
		setInput("");
	};

	return (
		<div className="flex flex-col h-full bg-[#101722]">
			<div className="flex-1 overflow-y-auto p-6 space-y-6">
				{messages
					.filter((msg) => !(msg.role === "assistant" && !msg.content))
					.map((msg) => (
						<div
							key={msg.id}
							className={`flex items-end gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
						>
							{/* Avatar */}
							<div
								className={`shrink-0 w-10 h-10 rounded-full border-2 ${
									msg.role === "assistant"
										? "bg-blue-600/20 border-blue-500 shadow-[0_0_15px_-3px_rgba(59,130,246,0.5)] flex items-center justify-center"
										: "bg-slate-800 border-slate-700"
								}`}
							>
								{msg.role === "assistant" ? (
									<Wand2 className="w-5 h-5 text-blue-400" />
								) : (
									<div className="w-full h-full bg-[url('https://api.dicebear.com/7.x/pixel-art/svg?seed=Adventurer')] bg-cover" />
								)}
							</div>

							<div
								className={`flex flex-col max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}
							>
								<span
									className={`text-[10px] font-bold uppercase tracking-widest mb-1 ${
										msg.role === "user" ? "text-slate-500" : "text-blue-500"
									}`}
								>
									{msg.role === "user" ? "Adventurer" : "The Oracle"}
								</span>

								<div
									className={`p-4 rounded-2xl text-sm leading-relaxed shadow-lg ${
										msg.role === "user"
											? "bg-blue-600 text-white rounded-br-none"
											: "bg-[#1a2436] text-slate-200 border border-slate-700 rounded-bl-none"
									}`}
								>
									{msg.role === "assistant" ? (
										<div className="prose prose-sm max-w-none prose-invert">
											<ReactMarkdown>{msg.content}</ReactMarkdown>
										</div>
									) : (
										<p className="whitespace-pre-wrap">{msg.content}</p>
									)}
								</div>
							</div>
						</div>
					))}

				{isCalculating && (
					<div className="flex items-end gap-3 flex-row animate-pulse">
						<div className="shrink-0 w-10 h-10 rounded-full border-2 bg-blue-600/20 border-blue-500 shadow-[0_0_15px_-3px_rgba(59,130,246,0.5)] flex items-center justify-center">
							<Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
						</div>
						<div className="flex flex-col items-start">
							<span className="text-[10px] font-bold uppercase tracking-widest mb-1 text-blue-500">
								The Oracle
							</span>
							<div className="p-4 rounded-2xl text-sm leading-relaxed shadow-lg bg-[#1a2436] text-slate-400 border border-slate-700 rounded-bl-none italic">
								{isCalculating === true
									? "Analyzing Response..."
									: (isCalculating as string)}
							</div>
						</div>
					</div>
				)}
				<div ref={messagesEndRef} />
			</div>

			<div className="p-6 bg-gradient-to-t from-[#101722] via-[#101722] to-transparent border-t border-slate-800/50 space-y-4">
				{canGenerate && (
					<button
						type="button"
						onClick={onSkip}
						className="group relative w-full py-4 px-6 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-black text-sm tracking-widest uppercase transition-all shadow-[0_0_20px_rgba(59,130,246,0.3)] active:scale-95 flex items-center justify-center gap-3 overflow-hidden"
					>
						<div className="absolute inset-0 bg-gradient-to-r from-blue-400/0 via-white/10 to-blue-400/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
						<Sparkles className="w-5 h-5 animate-pulse" />
						FORGE QUEST ROADMAP ({score}%)
					</button>
				)}

				<form onSubmit={handleSubmit} className="relative group">
					<div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl opacity-20 group-hover:opacity-40 transition duration-500 blur"></div>
					<div className="relative flex items-center bg-[#151e2e] border border-slate-700 rounded-2xl overflow-hidden px-4">
						<textarea
							rows={1}
							value={input}
							onChange={(e) => setInput(e.target.value)}
							onKeyDown={(e) => {
								if (e.key === "Enter" && !e.shiftKey) {
									e.preventDefault();
									handleSubmit(e);
								}
							}}
							placeholder="Describe your ambitions..."
							className="flex-1 py-4 bg-transparent text-white placeholder-slate-500 text-sm focus:outline-none resize-none"
							disabled={!!isCalculating}
						/>
						<button
							type="submit"
							className="p-2 text-blue-500 hover:text-blue-400 transition-colors disabled:opacity-50"
							disabled={!!isCalculating || !input.trim()}
						>
							<Send className="w-6 h-6" />
						</button>
					</div>
				</form>
			</div>
		</div>
	);
};

export default ChatPanel;
