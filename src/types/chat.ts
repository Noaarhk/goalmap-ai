export type MessageRole = "user" | "assistant";

export interface Message {
    id: string;
    role: MessageRole;
    content: string;
    timestamp: number;
}

export interface Conversation {
    id: string;
    title: string | null;
    messages: Message[];
    createdAt: number;
    updatedAt: number;
}
