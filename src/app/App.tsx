import { Loader2 } from "lucide-react";
import { useEffect } from "react";
import TransitionView from "../components/common/TransitionView";
import { AuthContainer } from "../features/auth/AuthContainer";
import { DiscoveryContainer } from "../features/discovery/DiscoveryContainer";
import { VisualizationContainer } from "../features/visualization/VisualizationContainer";
import { useAppStore, useAuthStore, useRoadmapStore } from "../stores";
import { AppState } from "../types";

function App() {
	const { appState } = useAppStore();
	const { roadmap } = useRoadmapStore();
	const { user, isLoading, isInitialized, initialize } = useAuthStore();

	// Initialize auth on mount
	useEffect(() => {
		initialize();
	}, [initialize]);

	// Show loading while initializing
	if (!isInitialized || isLoading) {
		return (
			<div className="flex h-screen w-screen bg-[#101722] items-center justify-center">
				<Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
			</div>
		);
	}

	// Show auth if not logged in
	if (!user) {
		return <AuthContainer />;
	}

	return (
		<div className="flex h-screen w-screen bg-[#101722] overflow-hidden text-slate-100">
			{appState === AppState.TRANSITION && <TransitionView />}

			{appState === AppState.DISCOVERY && <DiscoveryContainer />}

			{appState === AppState.VISUALIZATION && roadmap && (
				<VisualizationContainer />
			)}
		</div>
	);
}

export default App;
