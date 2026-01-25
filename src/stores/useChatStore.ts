import { create } from "zustand/react";
import type { Message, MessageRole } from "../types";

interface ChatStore {
    messages: Message[];

    currentConversationId: string | null;
    isLoading: boolean;

    // Actions
    addMessage: (role: MessageRole, content: string) => void;
    setMessages: (messages: Message[]) => void;
    setCurrentConversationId: (id: string | null) => void;
    loadConversation: (id: string, messages: Message[]) => void;
    reset: () => void;
}

const INITIAL_MESSAGE: Message = {
    id: "1",
    role: "assistant",
    content:
        "Greetings, Traveler. I am the Oracle. Describe the ultimate quest you seek to conquer, and together we shall forge a path to victory.",
    timestamp: Date.now(),
};

export const useChatStore = create<ChatStore>((set) => ({
    messages: [INITIAL_MESSAGE],
    currentConversationId: null,
    isLoading: false,

    addMessage: (role, content) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    id: Date.now().toString(),
                    role,
                    content,
                    timestamp: Date.now(),
                },
            ],
        })),

    setMessages: (messages) => set({ messages }),
    setCurrentConversationId: (id) => set({ currentConversationId: id }),
    loadConversation: (id, messages) => set({ currentConversationId: id, messages: messages.length > 0 ? messages : [INITIAL_MESSAGE] }),
    reset: () => set({ messages: [INITIAL_MESSAGE], currentConversationId: null, isLoading: false }),
}));
