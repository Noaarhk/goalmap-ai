export interface BlueprintData {
	goal?: string;
	why?: string;
	timeline?: string;
	obstacles?: string;
	resources?: string;
	fieldScores?: {
		goal: number;
		why: number;
		timeline: number;
		obstacles: number;
		resources: number;
	};
	readinessTips?: string[];
	successTips?: string[];
}


