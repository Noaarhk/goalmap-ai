import { create } from "zustand/react";
import { AppState, type TemplateType } from "../types";

interface AppStore {
    appState: AppState;
    template: TemplateType;

    // Actions
    setAppState: (state: AppState) => void;
    setTemplate: (type: TemplateType) => void;
}

export const useAppStore = create<AppStore>((set) => ({
    appState: AppState.DISCOVERY,
    template: "quest",

    setAppState: (appState) => set({ appState }),
    setTemplate: (template) => set({ template }),
}));
