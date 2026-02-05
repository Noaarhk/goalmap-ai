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

            // Convert snake_case keys to camelCase (API sends snake_case)
            const rawData = data as any;
            const normalizedData: Partial<BlueprintData> = {
                ...data,
                fieldScores: rawData.field_scores || data.fieldScores,
                readinessTips: rawData.readiness_tips || data.readinessTips,
                successTips: rawData.success_tips || data.successTips,
            };
            // Remove snake_case keys after conversion
            delete (normalizedData as any).field_scores;
            delete (normalizedData as any).readiness_tips;
            delete (normalizedData as any).success_tips;

            // Merge top-level fields (only if not null/undefined)
            for (const key in normalizedData) {
                if (key !== 'fieldScores' && normalizedData[key as keyof BlueprintData] !== null && normalizedData[key as keyof BlueprintData] !== undefined) {
                    (newBlueprint as any)[key] = normalizedData[key as keyof BlueprintData];
                }
            }

            // Deep merge fieldScores specifically
            if (normalizedData.fieldScores) {
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
                        Object.entries(normalizedData.fieldScores).filter(
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

