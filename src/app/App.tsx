import TransitionView from "../components/common/TransitionView";
import { DiscoveryContainer } from "../features/discovery/DiscoveryContainer";
import { VisualizationContainer } from "../features/visualization/VisualizationContainer";
import { useAppStore, useRoadmapStore } from "../stores";
import { AppState } from "../types";

function App() {
	const { appState } = useAppStore();
	const { roadmap } = useRoadmapStore();

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
