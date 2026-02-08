import { create } from "zustand";
import { persist } from "zustand/middleware";
import { AppState, type TemplateType } from "../types";

interface AppStore {
    appState: AppState;
    template: TemplateType;

    // Actions
    setAppState: (state: AppState) => void;
    setTemplate: (type: TemplateType) => void;
}

export const useAppStore = create<AppStore>()(
    persist(
        (set) => ({
            appState: AppState.DISCOVERY,
            template: "quest",

            setAppState: (appState) => set({ appState }),
            setTemplate: (template) => set({ template }),
        }),
        {
            name: "app-storage",
            partialize: (state) => ({ appState: state.appState }),
            merge: (_persisted, current) => {
                const persisted = _persisted as Partial<AppStore> | null;
                const restoredState = persisted?.appState;
                // TRANSITION is a transient streaming state — can't survive a refresh
                const safeState =
                    restoredState === AppState.TRANSITION
                        ? AppState.DISCOVERY
                        : restoredState ?? current.appState;
                return { ...current, appState: safeState };
            },
        }
    )
);
