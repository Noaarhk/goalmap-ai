import { create } from "zustand/react";
import type { Message, MessageRole } from "../types";

interface ChatStore {
    messages: Message[];

    // Actions
    addMessage: (role: MessageRole, content: string) => void;
    setMessages: (messages: Message[]) => void;
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
}));
