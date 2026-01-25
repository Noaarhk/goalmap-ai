import type { Session, User } from "@supabase/supabase-js";
import { create } from "zustand";
import { supabase } from "../services/supabase";
import { useBlueprintStore } from "./useBlueprintStore";
import { useChatStore } from "./useChatStore";
import { useRoadmapStore } from "./useRoadmapStore";

interface AuthState {
	user: User | null;
	session: Session | null;
	isLoading: boolean;
	isInitialized: boolean;

	// Actions
	initialize: () => Promise<void>;
	signIn: (email: string, password: string) => Promise<{ error: string | null }>;
	signUp: (email: string, password: string) => Promise<{ error: string | null }>;
	signInWithGoogle: () => Promise<{ error: string | null }>;
	signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, _get) => ({
	user: null,
	session: null,
	isLoading: false,
	isInitialized: false,

	initialize: async () => {
		try {
			// Get current session
			const {
				data: { session },
			} = await supabase.auth.getSession();

			set({
				user: session?.user ?? null,
				session,
				isInitialized: true,
			});

			// Listen for auth changes
			supabase.auth.onAuthStateChange((_event, session) => {
				if (!session) {
					// Reset all stores on logout/session expiry
					useBlueprintStore.getState().reset();
					useChatStore.getState().reset();
					useRoadmapStore.getState().reset();
				}
				set({
					user: session?.user ?? null,
					session,
				});
			});
		} catch (error) {
			console.error("Auth initialization error:", error);
			set({ isInitialized: true });
		}
	},

	signIn: async (email: string, password: string) => {
		set({ isLoading: true });
		try {
			const { data, error } = await supabase.auth.signInWithPassword({
				email,
				password,
			});

			if (error) {
				return { error: error.message };
			}

			set({
				user: data.user,
				session: data.session,
			});

			return { error: null };
		} finally {
			set({ isLoading: false });
		}
	},

	signUp: async (email: string, password: string) => {
		set({ isLoading: true });
		try {
			const { data, error } = await supabase.auth.signUp({
				email,
				password,
			});

			if (error) {
				return { error: error.message };
			}

			// Note: User might need to confirm email depending on Supabase settings
			if (data.user && !data.session) {
				return { error: "Please check your email to confirm your account." };
			}

			set({
				user: data.user,
				session: data.session,
			});

			return { error: null };
		} finally {
			set({ isLoading: false });
		}
	},

	signInWithGoogle: async () => {
		set({ isLoading: true });
		try {
			const { error } = await supabase.auth.signInWithOAuth({
				provider: "google",
				options: {
					redirectTo: window.location.origin,
				},
			});
			if (error) return { error: error.message };
			return { error: null };
		} finally {
			set({ isLoading: false });
		}
	},

	signOut: async () => {
		set({ isLoading: true });
		try {
			await supabase.auth.signOut();
			
			// Reset all stores
			useBlueprintStore.getState().reset();
			useChatStore.getState().reset();
			useRoadmapStore.getState().reset();

			set({ user: null, session: null });
		} finally {
			set({ isLoading: false });
		}
	},
}));
