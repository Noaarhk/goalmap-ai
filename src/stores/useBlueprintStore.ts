import { create } from "zustand/react";
import type { BlueprintData } from "../types";

interface BlueprintStore {
    blueprint: BlueprintData;
    isChatLoading: boolean | string;
    isBlueprintLoading: boolean;

    // Actions
    setBlueprint: (data: BlueprintData) => void;
    updateBlueprint: (data: Partial<BlueprintData>) => void;
    setIsChatLoading: (isLoading: boolean | string) => void;
    setIsBlueprintLoading: (isLoading: boolean) => void;
    reset: () => void;
}


export const useBlueprintStore = create<BlueprintStore>((set) => ({
    blueprint: {},
    isChatLoading: false,
    isBlueprintLoading: false,

    setBlueprint: (blueprint) => set({ blueprint }),
    updateBlueprint: (data) =>
        set((state) => {
            const newBlueprint = { ...state.blueprint };

            // Merge top-level fields (only if not null/undefined)
            for (const key in data) {
                if (key !== 'fieldScores' && data[key as keyof BlueprintData] !== null && data[key as keyof BlueprintData] !== undefined) {
                    (newBlueprint as any)[key] = data[key as keyof BlueprintData];
                }
            }

            // Deep merge fieldScores specifically
            if (data.fieldScores) {
                newBlueprint.fieldScores = {
                    ...(newBlueprint.fieldScores || {
                        goal: 0,
                        why: 0,
                        milestones: 0,
                        timeline: 0,
                        obstacles: 0,
                        resources: 0,
                    }),
                    ...Object.fromEntries(
                        Object.entries(data.fieldScores).filter(
                            ([_, v]) => v !== null && v !== undefined,
                        ),
                    ),
                } as any;
            }


            return { blueprint: newBlueprint };
        }),

    setIsChatLoading: (isChatLoading) => set({ isChatLoading }),
    setIsBlueprintLoading: (isBlueprintLoading) => set({ isBlueprintLoading }),
    reset: () => set({ blueprint: {}, isChatLoading: false, isBlueprintLoading: false }),
}));

